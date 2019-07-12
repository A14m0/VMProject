#!/usr/bin/env python3
import argparse
from importlib import reload
import os
if os.path.exists(".runInit"):
    import files.zombie as z
else:
    import zombie as z
    print("""[!] WARN: You appear to be running the runner for the first time!
          It is possible that you are running an outdated zombie file.
          If any errors occur during actual execution (after initialization),
          just try running the program again and it should work!""")

def main():
    

    parser = argparse.ArgumentParser(description="Synchronizes executions across multiple machines")
    parser.add_argument("ip", help="The IP of the controller server")
    parser.add_argument('type', help="Define the execution profile")
    parser.add_argument("-p","--port", help="Target server port. Default is 1337", nargs='?', default=1337, type=int)

    args = parser.parse_args()

    if args.type not in ["rando", "tester", "cpu"]:
        print("[-] Illegal type argument: '%s'" % args.type)
        return 1

    try:
        numClients = z.init(args.ip, args.port)
        reload(z)
        os.system('touch .runInit')
        z.log("[+] Initialization complete")

        zom = z.Zombie(args.ip, args.port, args.type, numClients)
        zom.start()
    except Exception as e:
        z.log("[-] Error. Killing all procs\n\tError: %s" % str(e))
        #print(traceback.format_exc())
        z.killall()

if __name__ == "__main__":
    main()