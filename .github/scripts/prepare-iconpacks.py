import os
import re
import sys
import shutil

iconpacks_dir = './iconpacks'
drawable_dir = './app/src/main/res/drawable'
arrays_file = './app/src/main/res/values/arrays.xml'
manifest_file = './app/src/main/AndroidManifest.xml'

VALID_DRAWABLE_EXTENSIONS = ['.xml', '.png', '.jpg', '.jpeg', '.webp']

def get_icon_packs():
    try:
        print("Fetching icon packs from:", iconpacks_dir)
        packs = [folder for folder in os.listdir(iconpacks_dir) if os.path.isdir(os.path.join(iconpacks_dir, folder))]
        print(f"Found {len(packs)} icon packs.")
        return packs
    except Exception as e:
        print(f"Error fetching icon packs: {e}")
        sys.exit(1)

def replace_drawable_references(content, package_name, pack_name_lower):
    search_pattern = '@drawable/'
    index = 0

    while index < len(content):
        index = content.find(search_pattern, index)
        if index == -1:
            break

        start = index + len(search_pattern)
        end = start

        while end < len(content) and (content[end].isalnum() or content[end] == '_'):
            end += 1

        drawable_name = content[start:end]
        new_drawable_name = f"{drawable_name}_{package_name}_{pack_name_lower}"

        print(f"Replacing {drawable_name} with {new_drawable_name}")

        content = content[:start] + new_drawable_name + content[end:]
        index = start + len(new_drawable_name)

    return content

def update_drawable_references():
    try:
        print("Updating drawable references...")

        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            pack_path = os.path.join(iconpacks_dir, pack_name)

            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    if package_name == 'com.android.systemui':
                        package_name = 'systemui'
                    elif package_name == 'com.android.settings':
                        package_name = 'settings'

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            file_path = os.path.join(package_path, file)

                            if file_extension == '.xml':
                                with open(file_path, 'r') as f:
                                    file_content = f.read()

                                updated_content = replace_drawable_references(file_content, package_name, pack_name_lower)

                                if updated_content != file_content:
                                    with open(file_path, 'w') as f:
                                        f.write(updated_content)
                                    print(f"Updated drawable references in: {file_path}")

        print("Drawable references updated successfully.")
    except Exception as e:
        print(f"Error updating drawable references: {e}")
        sys.exit(1)

def copy_and_rename_files():
    update_drawable_references()

    try:
        print("Starting file copy and rename process...")
        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            pack_path = os.path.join(iconpacks_dir, pack_name)
            print(f"Processing pack: {pack_name} ({pack_name_lower})")

            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)
                if os.path.isdir(package_path):
                    if package_name == 'com.android.systemui':
                        package_name = 'systemui'
                    elif package_name == 'com.android.settings':
                        package_name = 'settings'

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            original_file_path = os.path.join(package_path, file)
                            new_file_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}{file_extension}"
                            new_file_path = os.path.join(drawable_dir, new_file_name)

                            print(f"Copying {original_file_path} to {new_file_path}")
                            shutil.copy(original_file_path, new_file_path)

        print("File copy and rename process completed.")
    except Exception as e:
        print(f"Error in file copy and rename process: {e}")
        sys.exit(1)

def update_manifest():
    try:
        print("Updating manifest file:", manifest_file)
        with open(manifest_file, 'r') as f:
            manifest_content = f.read()

        start_comment = '<!-- START OF ICON PACKS -->'
        end_comment = '<!-- END OF ICON PACKS -->'
        start_idx = manifest_content.find(start_comment)
        end_idx = manifest_content.find(end_comment)

        if start_idx == -1 or end_idx == -1:
            print("Error: Comment markers not found in manifest file.")
            sys.exit(1)

        activities = ""
        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            activities += f"""
    <activity android:name="{pack_name_lower}"
        android:label="{pack_name}"
        android:exported="true">
        <intent-filter>
            <action android:name="sh.siava.pixelxpert.iconpack" />
            <category android:name="android.intent.category.DEFAULT" />
        </intent-filter>
    </activity>
"""

        new_manifest_content = (
            manifest_content[:start_idx + len(start_comment)] +
            activities +
            manifest_content[end_idx:]
        )

        with open(manifest_file, 'w') as f:
            f.write(new_manifest_content)
        print("Manifest file updated successfully.")
    except Exception as e:
        print(f"Error updating manifest: {e}")
        sys.exit(1)

def update_arrays():
    try:
        print("Updating arrays file:", arrays_file)
        with open(arrays_file, 'r') as f:
            arrays_content = f.read()

        start_resources = arrays_content.find('<resources>')
        end_resources = arrays_content.find('</resources>')

        if start_resources == -1 or end_resources == -1:
            print("Error: <resources> tags not found in arrays file.")
            sys.exit(1)

        array_updates = ""

        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())

            array_updates += f"""
<string-array name="{pack_name_lower}">
    <item>mapping_source_{pack_name_lower}</item>
    <item>replacement_{pack_name_lower}</item>
</string-array>
"""

            array_updates += f"""
<string-array name="mapping_source_{pack_name_lower}">
"""
            pack_path = os.path.join(iconpacks_dir, pack_name)
            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            array_updates += f"    <item>{package_name}:{os.path.splitext(file)[0]}</item>\n"
            array_updates += f"</string-array>\n"

            array_updates += f"""
<string-array name="replacement_{pack_name_lower}">
"""
            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    if package_name == 'com.android.systemui':
                        package_name = 'systemui'
                    elif package_name == 'com.android.settings':
                        package_name = 'settings'

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            new_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}"
                            array_updates += f"    <item>{new_name}</item>\n"
            array_updates += f"</string-array>\n"

        new_arrays_content = arrays_content[:start_resources + len('<resources>')] + array_updates + arrays_content[end_resources:]

        with open(arrays_file, 'w') as f:
            f.write(new_arrays_content)
        print("Arrays file updated successfully.")
    except Exception as e:
        print(f"Error updating arrays file: {e}")
        sys.exit(1)

def main():
    print("Starting automation script...")
    copy_and_rename_files()
    update_manifest()
    update_arrays()
    print("Automation script completed successfully.")

if __name__ == '__main__':
    print(f"Python version: {sys.version}")
    print("Running main logic...")
    main()
