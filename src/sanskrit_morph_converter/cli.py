import argparse
import json
import sys
from pathlib import Path

def run_update(args):
    """Handles the 'morph update' command."""
    # Import here to keep the CLI extremely fast if they are just running 'convert'
    from .compiler import compile_mappings
    
    print("=" * 50)
    print("🔄 Sanskrit Morph Converter - Data Updater")
    print("=" * 50)
    print("Fetching the latest morphological mappings from Google Sheets...")
    
    try:
        compile_mappings()
        print("-" * 50)
        print("✅ Success! TSV files have been updated.")
        print("=" * 50)
    except Exception as e:
        print("-" * 50)
        print(f"❌ Error during compilation: {e}")
        print("=" * 50)
        sys.exit(1)

def run_convert(args):
    """Handles the 'morph convert' command."""
    from .converter import RepresentationConverter
    
    inputs_list = []
    if args.input:
        try:
            parsed = json.loads(args.input)
            inputs_list = [parsed] if isinstance(parsed, dict) else parsed
        except json.JSONDecodeError:
            # Fallback if it's just a regular string like "m. sg. nom."
            inputs_list = [args.input]
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: File not found at {args.file}")
            sys.exit(1)
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                inputs_list = data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            with open(file_path, 'r', encoding='utf-8') as f:
                inputs_list = [line.strip() for line in f if line.strip()]

    converter = RepresentationConverter()
    
    if len(inputs_list) == 1:
        try:
            res = converter.convert(args.source, args.target, inputs_list[0], args.format, args.output_script, args.input_script)
            
            # --- DYNAMIC STATUS LOGIC FOR CLI ---
            if isinstance(res, list):
                if len(res) > 1: status = "Ambiguous"
                elif len(res) == 1: status = "Success"
                else: status = "Unrecognized"
            elif isinstance(res, dict):
                morphs = res.get('morph', [])
                if not morphs: status = "Unrecognized"
                elif len(morphs) > 1 or sum(len(m.get('inflectional_morphs', [])) for m in morphs) > 1:
                    status = "Ambiguous"
                else: status = "Success"
            else:
                status = "Success"
                
            final_output = [{"input": inputs_list[0], "output": res, "status": status}]
            
        except Exception as e:
            final_output = [{"input": inputs_list[0], "output": str(e), "status": "Error"}]
    else:
        final_output = converter.convert_bulk(args.source, args.target, inputs_list, args.format, args.output_script, args.input_script)

    out_str = json.dumps(final_output, indent=2, ensure_ascii=False)
    
    if args.output:
        out_path = Path(args.output)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out_str)
        print(f"✅ Successfully processed {len(inputs_list)} items.")
        print(f"📁 Results saved to: {out_path.absolute()}")
    else:
        print(out_str)


def main():
    parser = argparse.ArgumentParser(
        description="Sanskrit Morph Converter (SMC): A universal mapping layer for Sanskrit Morphological Analysis."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- SUBCOMMAND 1: update ---
    parser_update = subparsers.add_parser("update", help="Fetch the latest TSV mappings from Google Sheets.")
    parser_update.set_defaults(func=run_update)

    # --- SUBCOMMAND 2: convert ---
    parser_convert = subparsers.add_parser("convert", help="Convert morphological tags between platforms.")
    parser_convert.add_argument("source", help="Source platform (e.g., DCS, SCL, ByT5, SH, Svarupa)")
    parser_convert.add_argument("target", help="Target platform (e.g., SH, DCS, ByT5, SCL, Svarupa)")
    parser_convert.add_argument("--format", choices=["json", "string"], default="json", help="Requested output format (default: json).")
    parser_convert.add_argument("-os", "--output-script", dest="output_script", help="Force an output script (e.g., IAST, Devanagari, WX). Overrides platform default.")
    parser_convert.add_argument("-is", "--input-script", dest="input_script", help="Specify the input script. Defaults to 'autodetect'.")
    
    group = parser_convert.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", help="A single string or JSON payload to convert.")
    group.add_argument("-f", "--file", help="Path to a text file or JSON file containing a list of inputs.")
    
    parser_convert.add_argument("-o", "--output", help="Path to save the JSON results. Prints to terminal if omitted.")
    parser_convert.set_defaults(func=run_convert)

    # Parse and route to the correct function
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()