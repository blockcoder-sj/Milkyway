"""Bounded personal detail collection, independent of streaming and ledger work."""
import time
from .provider_process import ProviderProcess
from . import sector_classifications
from .config import get_settings
from .database import RuntimeHeartbeat,SessionLocal,prepare_runtime_database,utcnow
from .market_catalog import CATALOG
from .market_details import REFRESH_SECONDS,_provider,refresh_detail,read_cache


def main():
    settings=get_settings()
    if not settings.personal_local_mode or settings.production:
        raise SystemExit('Market detail worker requires personal mode')
    if settings.startup_errors('deployment'):
        raise SystemExit('Invalid personal configuration')
    prepare_runtime_database()
    classifications = ProviderProcess(sector_classifications.collect)
    try:
        while True:
            check = sector_classifications.read(settings)
            if check.attempted_at is None or (utcnow()-check.attempted_at).total_seconds()>=sector_classifications.REFRESH_SECONDS:
                try:
                    sector_classifications.refresh(settings, classifications)
                except (OSError,ValueError,RuntimeError,TimeoutError):
                    pass
            for instrument in CATALOG:
                cache=read_cache(settings,instrument.id)
                when=cache.attempted_at
                if when is None or when.tzinfo is None or (utcnow()-when).total_seconds()>=REFRESH_SECONDS:
                    try:
                        refresh_detail(settings,instrument.id)
                    except (OSError,ValueError,RuntimeError):
                        pass
                with SessionLocal() as session:
                    row=session.get(RuntimeHeartbeat,'market-details')
                    if row is None:
                        row=RuntimeHeartbeat(component='market-details',instance_id='personal-market-details')
                    row.observed_at,row.detail=utcnow(),'display detail '+instrument.id
                    session.add(row);session.commit()
                time.sleep(.2)
            time.sleep(15)
    finally:
        _provider.close()
        classifications.close()


if __name__=='__main__':
    main()
