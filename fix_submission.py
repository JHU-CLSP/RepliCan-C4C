import yaml
import json
import os
import re
from pathlib import Path

def fix_submission_file(input_file, output_file=None):
    """
    Fix submission file to meet validation requirements
    """
    if output_file is None:
        output_file = input_file
    
    try:
        # Load the file (try YAML first, then JSON)
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                f.seek(0)
                data = json.load(f)
        
        # Fix required fields
        fixed_data = {
            'username': data.get('username', ''),
            'paper_title': data.get('paper_title', ''),
            'paper_pdf': data.get('paper_pdf', ''),
            'identifier': data.get('identifier', ''),
            'claim_type': 'custom_code',  # Add required claim_type field
            'code_url': data.get('code_url', 'NOT_SPECIFIED'),
            'data_url': data.get('data_url', 'NOT_SPECIFIED'),  # Optional but keep if present
            'claims': [],
            'non_reproducible_claims': data.get('non_reproducible_claims', [])
        }
        
        # Fix claims
        if 'claims' in data and data['claims']:
            for claim in data['claims']:
                fixed_claim = {
                    'claim': claim.get('claim', ''),
                    'instruction': []
                }
                
                # Fix instruction format
                instructions = claim.get('instruction', [])
                if isinstance(instructions, str):
                    # Convert string to list
                    instructions = [instructions]
                
                # Clean up instructions - remove numbering and fix format
                cleaned_instructions = []
                for inst in instructions:
                    if isinstance(inst, str):
                        # Remove leading numbers and dots
                        cleaned = re.sub(r'^\s*\d+\.\s*', '', inst.strip())
                        # Remove trailing periods
                        cleaned = cleaned.rstrip('.')
                        if cleaned:
                            cleaned_instructions.append(cleaned)
                    else:
                        cleaned_instructions.append(str(inst))
                
                fixed_claim['instruction'] = cleaned_instructions
                fixed_data['claims'].append(fixed_claim)
        
        # Validate URLs
        url_fields = ['paper_pdf', 'code_url', 'data_url']
        for field in url_fields:
            if field in fixed_data and fixed_data[field]:
                url = fixed_data[field]
                if url != 'NOT_SPECIFIED' and not (url.startswith('http://') or url.startswith('https://')):
                    print(f"Warning: {field} URL doesn't start with http:// or https://")
        
        # Write fixed file
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(fixed_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"✅ Successfully fixed {input_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {input_file}: {str(e)}")
        return False

def validate_filename(filename):
    """
    Validate filename contains only allowed characters
    """
    # Remove directory path for validation
    basename = os.path.basename(filename)
    # Check if filename contains only letters, numbers, underscores, hyphens, and dots
    if re.match(r'^[a-zA-Z0-9_.-]+$', basename):
        return True, basename
    else:
        # Suggest a fixed filename
        fixed_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
        return False, fixed_name

def batch_fix_submissions(input_directory, output_directory=None):
    """
    Batch fix all submission files in a directory
    """
    input_path = Path(input_directory)
    
    if output_directory:
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path
    
    # Find all YAML and JSON files
    submission_files = list(input_path.glob("*.yaml")) + list(input_path.glob("*.yml")) + list(input_path.glob("*.json"))
    
    if not submission_files:
        print(f"No submission files found in {input_directory}")
        return
    
    successful = 0
    failed = 0
    
    for file_path in submission_files:
        # Validate and fix filename if needed
        is_valid, suggested_name = validate_filename(file_path.name)
        
        if output_directory:
            if is_valid:
                output_file = output_path / file_path.name
            else:
                output_file = output_path / suggested_name
                print(f"📝 Renaming {file_path.name} to {suggested_name}")
        else:
            if not is_valid:
                new_path = file_path.parent / suggested_name
                print(f"📝 Will rename {file_path.name} to {suggested_name}")
                output_file = new_path
            else:
                output_file = file_path
        
        if fix_submission_file(file_path, output_file):
            successful += 1
        else:
            failed += 1
    
    print(f"\n📊 Batch processing complete:")
    print(f"✅ Successfully processed: {successful} files")
    print(f"❌ Failed: {failed} files")

def create_workflow_safe_script():
    """
    Create a shell script snippet that handles filenames safely
    """
    script_content = '''#!/bin/bash

# Safe way to handle file lists in GitHub Actions workflow
# This should replace problematic sections in .github/workflows/validate-pr.yml

# Get list of changed files safely
mapfile -t changed_files < <(git diff --name-only --diff-filter=A HEAD~1 HEAD | grep "^submissions/")

if [ ${#changed_files[@]} -eq 0 ]; then
    echo "❌ No submission files found in this PR"
    exit 1
fi

echo "📁 Found ${#changed_files[@]} submission files:"
for file in "${changed_files[@]}"; do
    echo "  - $file"
done

# Validate each file
for file in "${changed_files[@]}"; do
    if [ -f "$file" ]; then
        echo "🔍 Validating: $file"
        python scripts/validate_submission.py "$file"
        if [ $? -ne 0 ]; then
            echo "❌ Validation failed for: $file"
            exit 1
        fi
    else
        echo "❌ File not found: $file"
        exit 1
    fi
done

echo "✅ All submission files validated successfully"
'''
    
    with open('fix_workflow.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('fix_workflow.sh', 0o755)
    print("📝 Created fix_workflow.sh - use this to replace problematic workflow sections")

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix submission files for validation')
    parser.add_argument('--input', '-i', default='submissions/', help='Input directory')
    parser.add_argument('--output', '-o', help='Output directory (optional)')
    parser.add_argument('--single', '-s', help='Fix single file')
    parser.add_argument('--create-workflow-fix', action='store_true', help='Create workflow fix script')
    
    args = parser.parse_args()
    
    if args.create_workflow_fix:
        create_workflow_safe_script()
    elif args.single:
        fix_submission_file(args.single)
    else:
        batch_fix_submissions(args.input, args.output)