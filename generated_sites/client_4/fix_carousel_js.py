import glob
import re

files = glob.glob('project-*.html')

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find incorrect line and replace
    new_content = re.sub(r'track\.style\.transform = \s*ranslateX\(-%\);', r'track.style.transform = `translateX(-${currentIndex * 100}%)`;', content)
    
    # Also fix project.html if it still has it
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)

print("Fixed syntax errors in js")
