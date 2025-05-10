import os

# Path to the documents.html template
template_path = os.path.join('frontend', 'template', 'client', 'documents.html')

# Read the template file
with open(template_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Replace the problematic code
fixed_content = content.replace('{{ document.get_type_display }}', '{{ document.get_type_display() }}')

# Write the fixed content back to the file
with open(template_path, 'w', encoding='utf-8') as file:
    file.write(fixed_content)

print(f"Fixed template at {template_path}")
