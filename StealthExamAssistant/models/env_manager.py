import os
from pathlib import Path

class EnvManager:
    """环境变量管理器：读写 .env 文件"""
    
    def __init__(self, env_path=".env"):
        self.env_path = Path(env_path)
        self._ensure_file()
        
    def _ensure_file(self):
        """确保 .env 文件存在"""
        if not self.env_path.exists():
            # 从 .env.example 复制
            example_path = self.env_path.parent / ".env.example"
            if example_path.exists():
                import shutil
                shutil.copy(example_path, self.env_path)
            else:
                self.env_path.touch()
                
    def read(self, key, default=""):
        """读取环境变量"""
        # 先从 os.environ 读取
        value = os.environ.get(key)
        if value:
            return value
            
        # 再从 .env 文件读取
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            return v.strip()
                            
        return default
        
    def write(self, key, value):
        """写入环境变量到 .env 文件"""
        lines = []
        found = False
        
        # 读取现有内容
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
        # 更新或添加
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                k, v = stripped.split('=', 1)
                if k.strip() == key:
                    new_lines.append(f"{key}={value}\n")
                    found = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        # 如果没找到，添加到末尾
        if not found:
            new_lines.append(f"{key}={value}\n")
            
        # 写入文件
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        # 同步到 os.environ
        os.environ[key] = value
        
    def read_all(self):
        """读取所有配置"""
        config = {}
        
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        config[k.strip()] = v.strip()
                        
        return config
        
    def write_batch(self, config_dict):
        """批量写入配置"""
        for key, value in config_dict.items():
            self.write(key, value)