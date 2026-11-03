"""The local launcher has fixed authority, authenticated HTTP and bounded recovery."""
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from deploy import local_control as control


class LocalControlTests(unittest.TestCase):
    def test_simultaneous_launchers_share_one_complete_capability(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/"control"
            with ThreadPoolExecutor(max_workers=6) as pool:values=list(pool.map(lambda _:control.owner_token(root),range(12)))
            self.assertEqual(len(set(values)),1)
            self.assertEqual(list(root.glob(".token-new-*")),[])

    def test_token_is_private_persistent_and_not_read_through_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/"control"
            first=control.owner_token(root)
            self.assertEqual(len(first),64)
            self.assertEqual(first,control.owner_token(root))
            if os.name!="nt":self.assertEqual((root/"token").stat().st_mode&0o777,0o600)
            (root/"token").unlink();(root/"token").symlink_to(Path(directory)/"other")
            with self.assertRaises((OSError,control.ControlError)):control.owner_token(root)

    def test_port_configuration_only_reads_a_valid_loopback_app_port(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{},clear=True):
            root=Path(directory);(root/".env").write_text('OTHER_SECRET=not-read\nMILKYWAY_PORT="18080"\n')
            self.assertEqual(control.app_port(root),18080)
            for value in ("19480","0","65536","8080;echo bad","http://evil"):
                with patch.dict(os.environ,{"MILKYWAY_PORT":value}):
                    with self.assertRaises(control.ControlError):control.app_port(root)

    def test_existing_services_are_started_without_recreation_or_image_changes(self):
        c=control.Controller(token="a"*64,port=8080)
        inventory={name:{"State":"running","ID":"a"*64} for name in control.SERVICES}
        inventory["paper-worker"]={"State":"exited","ID":"b"*64}
        with patch.object(c,"_inventory",return_value=inventory),patch.object(c,"compose") as compose,patch.object(c,"command") as command:
            c._start_services(False)
            compose.assert_not_called()
            command.assert_called_once_with(["start","b"*64],timeout=45)

    def test_monitor_reports_stopped_process_even_with_a_recent_saved_heartbeat(self):
        c=control.Controller(token="a"*64,port=8080)
        with patch.object(c,"_inventory",return_value={"paper-worker":{"State":"exited"},"app":{"State":"running"}}) as inspect:
            first=c.services();second=c.services()
        self.assertTrue(first["available"])
        self.assertEqual(first["services"]["paper-worker"],"exited")
        self.assertEqual(first,second);inspect.assert_called_once_with(timeout=4)

    def test_only_missing_allowlisted_service_is_created_and_no_volume_operation_exists(self):
        c=control.Controller(token="a"*64,port=8080)
        inventory={name:{"State":"running","ID":"a"*64} for name in control.SERVICES if name!="paper-worker"}
        with patch.object(c,"_inventory",return_value=inventory),patch.object(c,"compose") as compose,patch.object(c,"command",return_value=Mock(returncode=0)):
            c._start_services(False)
            compose.assert_called_once_with("up","-d","--no-deps","--no-build","paper-worker",timeout=90)
        self.assertEqual(set(control.SERVICES),{"app","paper-worker","personal-data","backtest-worker","market-data","market-details","backup"})

    def test_recovery_restarts_only_stale_worker_and_resumes_exact_account(self):
        c=control.Controller(token="a"*64,port=8080)
        healthy={"workers":{name:{"alive":True,"detail":"ok"} for name in ("paper-worker","personal-data","backtest-worker")}}
        stale={"workers":{**healthy["workers"],"paper-worker":{"alive":False}}}
        calls=[]
        def command(name,account_id=None,input=None):
            calls.append((name,account_id,input))
            if name=="pair-control":return {"paired":True}
            if name=="doctor":return stale if len([x for x in calls if x[0]=="doctor"])==1 else healthy
            return {"account_id":account_id,"resumed":True}
        with patch.object(c,"_start_docker"),patch.object(c,"_start_services"),patch.object(c,"_wait_web"),patch.object(c,"_app_command",side_effect=command),patch.object(c,"compose") as compose:
            c._recover("b"*32,False)
        self.assertEqual(c.status()["state"],"complete")
        compose.assert_called_once_with("restart","paper-worker",timeout=60)
        self.assertIn(("resume","b"*32,None),calls)

    def test_unavailable_docker_never_claims_success_or_resumes_accounts(self):
        c=control.Controller(token="a"*64,port=8080)
        with patch.object(c,"_start_docker",side_effect=control.ControlError("Docker 대기")),patch.object(c,"_app_command") as app:
            c._recover(None,False)
        self.assertEqual(c.status()["state"],"failed")
        self.assertFalse(c.status()["busy"])
        app.assert_not_called()

    def test_concurrent_clicks_share_one_recovery_job(self):
        c=control.Controller(token="a"*64,port=8080)
        gate=threading.Event();started=threading.Event()
        def work(*_args):started.set();gate.wait(3)
        with patch.object(c,"_recover",side_effect=work) as recover:
            with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda _:c.recover("b"*32),range(12)))
            self.assertTrue(started.wait(1));self.assertTrue(all(r["busy"] for r in results));self.assertEqual(recover.call_count,1)
            gate.set()


class LocalControlHttpTests(unittest.TestCase):
    def setUp(self):
        self.controller=control.Controller(token="a"*64,port=8080)
        self.controller.recover=Mock(return_value={"state":"running","busy":True,"message":"synthetic"})
        self.server=control.LocalControlServer(("127.0.0.1",0),control.handler_for(self.controller))
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":.02},daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)

    def request(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection("127.0.0.1",self.server.server_address[1],timeout=3)
        fields={"Host":"127.0.0.1:19480","Origin":"http://localhost:8080","Authorization":"Bearer "+"a"*64}
        if body is not None:fields["Content-Type"]="application/json"
        fields.update(headers or {})
        connection.request(method,path,json.dumps(body) if body is not None else None,fields)
        response=connection.getresponse();result=(response.status,dict(response.headers),json.loads(response.read()));connection.close();return result

    def test_exact_origin_host_and_capability_are_all_required(self):
        status,headers,_=self.request("GET","/v1/status")
        self.assertEqual(status,200);self.assertEqual(headers["Access-Control-Allow-Origin"],"http://localhost:8080")
        for header in ({"Origin":"https://evil.example"},{"Origin":"null"},{"Host":"evil.example:19480"},{"Authorization":""}):
            with self.subTest(header=header):self.assertEqual(self.request("POST","/v1/recover",{},header)[0],403)
        self.controller.recover.assert_not_called()

    def test_get_does_not_recover_and_unknown_commands_and_invalid_ids_are_rejected(self):
        self.assertEqual(self.request("GET","/v1/recover")[0],404)
        self.assertEqual(self.request("POST","/v1/delete",{})[0],404)
        for body in ({"command":"down -v"},{"account_id":"../../other"},{"account_id":3},{"path":"/tmp"}):
            # The real controller, not a permissive mock, validates account IDs.
            self.controller.recover=control.Controller.recover.__get__(self.controller)
            with patch.object(self.controller,"_recover") as work:
                self.assertEqual(self.request("POST","/v1/recover",body)[0],422)
                work.assert_not_called()

    def test_preflight_is_restricted_and_valid_recovery_is_authenticated(self):
        self.assertEqual(self.request("OPTIONS","/v1/recover",headers={"Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"authorization,content-type"})[0],200)
        status,headers,_=self.request("OPTIONS","/v1/recover",headers={"Origin":"https://evil.example","Access-Control-Request-Method":"POST"})
        self.assertEqual(status,403);self.assertNotIn("Access-Control-Allow-Origin",headers)
        self.assertEqual(self.request("POST","/v1/recover",{"account_id":"b"*32})[0],202)
        self.controller.recover.assert_called_once_with("b"*32)

    def test_local_client_never_follows_redirects_with_the_capability(self):
        from http.server import BaseHTTPRequestHandler
        class Redirect(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302);self.send_header("Location","https://outside.invalid/never");self.end_headers()
            def log_message(self,*_args):pass
        server=control.LocalControlServer(("127.0.0.1",0),Redirect)
        thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":.02},daemon=True);thread.start()
        try:
            with self.assertRaises(control.ControlError):control.loopback_json("http://127.0.0.1:{}/".format(server.server_address[1]),token="a"*64)
        finally:
            server.shutdown();server.server_close();thread.join(2)
