import yaml
import os
from pathlib import Path

def fix_code_url(file_path):
    """
    Fix code_url for files where it's empty or NOT_SPECIFIED
    """
    try:
        # Load YAML file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Check and fix code_url
        code_url = data.get('code_url', '')
        if not code_url or code_url == 'NOT_SPECIFIED' or code_url.strip() == '':
            data['code_url'] = 'http://www.quantum-espresso.org/download'
            print(f"✅ Fixed code_url in {file_path}")
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            return True
        else:
            print(f"ℹ️  code_url already valid in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def batch_fix_code_urls(directory):
    """
    Fix code_url in all YAML files in directory
    """
    path = Path(directory)
    yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))
    
    if not yaml_files:
        print(f"No YAML files found in {directory}")
        return
    
    fixed_count = 0
    for file_path in yaml_files:
        if fix_code_url(file_path):
            fixed_count += 1
    
    print(f"\n📊 Fixed {fixed_count} out of {len(yaml_files)} files")

# Usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Fix specific file or directory
        target = sys.argv[1]
        if os.path.isfile(target):
            fix_code_url(target)
        elif os.path.isdir(target):
            batch_fix_code_urls(target)
        else:
            print(f"❌ {target} is not a valid file or directory")
    else:
        # Default to submissions directory
        batch_fix_code_urls("submissions/")