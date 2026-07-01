import sys
import SPLMeter as spl

def main():
    simulate = "--simulate" in sys.argv
    wav_path = None

    if simulate:
        idx = sys.argv.index("--simulate")
        if idx + 1 < len(sys.argv):
            wav_path = sys.argv[idx + 1]
        else:
            print("Usage: python3 main.py --simulate <path/to/file.wav>")
            sys.exit(1)

    splMeter = spl.SPLMeter(simulate=simulate, wav_path=wav_path)
    splMeter.run()

if __name__ == "__main__":
    main()
