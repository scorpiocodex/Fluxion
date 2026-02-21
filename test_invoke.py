import traceback
import sys
from fluxion.cli.app import app

sys.argv = ['fluxion', 'fetch', 'ipfs://QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG/readme', '-o', 'test_ipfs.txt']

try:
    import fluxion.cli.app
    original_handle_error = fluxion.cli.app._handle_error

    def fake_handle(hud, exc, trace=False):
        print(f"TRAPPED IN HANDLE_ERROR! {type(exc)} -> repr: {repr(exc)}")
        print(f"exc.message = {getattr(exc, 'message', '<MISSING>')}")
        print(f"exc.__str__() = {str(exc)}")
        traceback.print_exc()

    fluxion.cli.app._handle_error = fake_handle
    app()
except SystemExit:
    pass
except Exception as e:
    print(f"UNHANDLED EXCEPTION: {repr(e)}")
    traceback.print_exc()
