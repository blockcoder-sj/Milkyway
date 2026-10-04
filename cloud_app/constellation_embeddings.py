"""Pinned local E5 encoder. Never downloads files or calls an inference provider."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

MODEL_REPO = 'intfloat/multilingual-e5-small'
MODEL_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
FILES = {
    'onnx/model_qint8_avx512_vnni.onnx': ('dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88', 118346824),
    'tokenizer.json': ('0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39', 17082730),
}
DIMENSIONS = 384
MAX_TOKENS = 256
_lock = threading.Lock()
_encoder = None
_query_lock = threading.Semaphore(1)


def model_directory(settings):
    if not settings.personal_local_mode or settings.production:
        raise ValueError('Local semantic model requires personal mode')
    return settings.dataset_dir.parent / 'research-models' / ('e5-' + MODEL_REVISION[:12])


def verify(directory):
    directory = Path(directory)
    for name, (expected, size) in FILES.items():
        path = directory / name
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or path.stat().st_size != size:
            raise ValueError('의미 검색 모델 파일이 없거나 안전한 일반 파일이 아닙니다.')
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(part)
        if digest.hexdigest() != expected:
            raise ValueError('의미 검색 모델의 SHA-256이 일치하지 않습니다.')


class Encoder:
    def __init__(self, directory):
        verify(directory)
        os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
        ort.disable_telemetry_events()
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        options.enable_mem_pattern = False
        options.add_session_config_entry('session.intra_op.allow_spinning', '0')
        self.session = ort.InferenceSession(str(Path(directory) / next(iter(FILES))), options,
                                           providers=['CPUExecutionProvider'])
        self.tokenizer = Tokenizer.from_file(str(Path(directory) / 'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding(pad_id=1)
        self.np = np
        self.lock = threading.Lock()

    def chunks(self, text):
        # Offsets preserve exact source text. No repeated vocabulary clones and
        # no silently truncated source tail; overlap spans every original token.
        with self.lock:
            self.tokenizer.no_truncation(); self.tokenizer.no_padding()
            try:
                offsets = self.tokenizer.encode(text, add_special_tokens=False).offsets
                parts=[]
                for i in range(0,len(offsets),168):
                    end=min(i+200,len(offsets))
                    parts.append(text[offsets[i][0]:offsets[end-1][1]])
                    if end==len(offsets):break
                return parts or ['']
            finally:
                self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
                self.tokenizer.enable_padding(pad_id=1)

    def encode(self, texts, *, query=False):
        np = self.np
        with self.lock:
            encodings = self.tokenizer.encode_batch([('query: ' if query else 'passage: ') + t for t in texts])
            ids = np.asarray([e.ids for e in encodings], dtype=np.int64)
            mask = np.asarray([e.attention_mask for e in encodings], dtype=np.int64)
            feed = {'input_ids': ids, 'attention_mask': mask}
            if any(i.name == 'token_type_ids' for i in self.session.get_inputs()):
                feed['token_type_ids'] = np.asarray([e.type_ids for e in encodings], dtype=np.int64)
            hidden = self.session.run(None, feed)[0]
            pooled = (hidden * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1)[:, None]
            normalized = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            if normalized.shape != (len(texts), DIMENSIONS) or not np.isfinite(normalized).all():
                raise ValueError('Invalid local embedding output')
            return normalized.astype('<f4')


def encoder(settings):
    global _encoder
    directory = model_directory(settings)
    with _lock:
        if _encoder is None or _encoder[0] != str(directory):
            _encoder = (str(directory), Encoder(directory))
        return _encoder[1]


def query_vector(settings, text):
    """Release the large model/tokenizer after each interactive query."""
    import numpy as np
    directory = model_directory(settings)
    if not _query_lock.acquire(timeout=1):
        raise ValueError('의미 검색이 진행 중입니다. 잠시 후 다시 시도하세요.')
    try:
        result = subprocess.run([sys.executable, '-m', 'cloud_app.constellation_embeddings', str(directory)],
                                input=json.dumps(text[:240]), capture_output=True, text=True, timeout=15,
                                env={**os.environ, 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1', 'TOKENIZERS_PARALLELISM':'false'})
    finally:
        _query_lock.release()
    if result.returncode:
        raise ValueError('로컬 의미 검색 모델을 실행하지 못했습니다.')
    vector = np.asarray(json.loads(result.stdout), dtype='<f4')
    if vector.shape != (DIMENSIONS,) or not np.isfinite(vector).all() or abs(float(np.linalg.norm(vector))-1)>.002:
        raise ValueError('Invalid isolated query vector')
    return vector


if __name__ == '__main__':
    value = json.loads(sys.stdin.read(4096))
    if not isinstance(value, str) or len(value)>240:
        raise SystemExit('Invalid local query')
    print(json.dumps(Encoder(sys.argv[1]).encode([value], query=True)[0].tolist()))
