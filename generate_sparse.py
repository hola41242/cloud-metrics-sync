import os, glob

target_dir = "/storage_root"
torrent_dir = "/config/torrents"
os.makedirs(target_dir, exist_ok=True)

def bdecode(data):
    def decode_item(idx):
        char = data[idx:idx+1]
        if char == b'i':
            idx += 1
            end = data.index(b'e', idx)
            return int(data[idx:end]), end + 1
        elif char == b'l':
            idx += 1
            res = []
            while data[idx:idx+1] != b'e':
                item, idx = decode_item(idx)
                res.append(item)
            return res, idx + 1
        elif char == b'd':
            idx += 1
            res = {}
            while data[idx:idx+1] != b'e':
                key, idx = decode_item(idx)
                val, idx = decode_item(idx)
                res[key.decode('utf-8', errors='ignore')] = val
            return res, idx + 1
        elif char.isdigit():
            colon = data.index(b':', idx)
            length = int(data[idx:colon])
            start = colon + 1
            return data[start:start+length], start + length
        else:
            raise ValueError(f"Invalid byte at index {idx}")
    res, _ = decode_item(0)
    return res

for tpath in glob.glob(os.path.join(torrent_dir, "*.torrent")):
    try:
        with open(tpath, "rb") as f:
            content = f.read()
        meta = bdecode(content)
        info = meta.get('info', {})
        name = info.get('name')
        if isinstance(name, bytes):
            name = name.decode('utf-8', errors='ignore')
        if not name:
            continue

        if 'files' in info:
            base_folder = os.path.join(target_dir, name)
            os.makedirs(base_folder, exist_ok=True)
            for f_entry in info['files']:
                length = f_entry.get('length', 0)
                raw_paths = [p.decode('utf-8', errors='ignore') if isinstance(p, bytes) else str(p) for p in f_entry.get('path', [])]
                file_rel_path = os.path.join(*raw_paths)
                full_p = os.path.join(base_folder, file_rel_path)
                os.makedirs(os.path.dirname(full_p), exist_ok=True)
                with open(full_p, "wb") as ghost:
                    ghost.truncate(length)
        else:
            length = info.get('length', 0)
            single_p = os.path.join(target_dir, name)
            os.makedirs(os.path.dirname(single_p), exist_ok=True)
            with open(single_p, "wb") as ghost:
                ghost.truncate(length)
    except Exception as e:
        print(f"Error creating sparse: {e}")
