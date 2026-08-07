import argparse
from adapter.providers.web_provider import WebProvider

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",nargs="?",default="version")
    args=p.parse_args()
    if args.command=="version":
        print("Nateks Legacy Adapter 0.2-dev")
    else:
        print("Command placeholder:",args.command)

if __name__=="__main__":
    main()
