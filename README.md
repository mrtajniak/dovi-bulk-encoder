# dovi-bulk-encoder

**dovi-bulk-encoder** is an automation tool designed for users performing bulk encoding of **Dolby Vision Profile 7** files.  
It requires an **active Dolby Encoding Engine (DEE) license**, as DEE serves as the underlying encoding backend.

---

## 🔍 How It Works

The script continuously monitors a specified directory for the presence of:

- **Video master file**  
  *Any input format supported by Dolby Encoding Engine (not limited to `.mov`)*
- **DolbyMetadata.xml**

When both files are detected, the script automatically triggers the **Dolby Vision encoding workflow**.

---

## ⚙️ Configuration

Because the project is built on top of **Dolby Encoding Engine**, all **DEE command-line arguments** are supported.  
You can provide them through a **JSON configuration file**.

The script also includes additional custom arguments, which can be viewed via:

```bash
python folder_watcher_dv7_encoder.py -h
```
or
```bash
python folder_watcher_dv7_encoder.py --help
```

## 🐍 Requirements

- **Python 3.13**  
  *(Compatibility with earlier versions has not been tested.)*
- **Active DEE license**
