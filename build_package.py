#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 将GEHistoricalImagery GUI应用程序打包成可执行文件夹
使用PyInstaller进行打包
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()
    
    # 定义源文件和目录
    main_script = current_dir / "map_app.py"
    coord_convert = current_dir / "coord_convert.py"
    gdal_dir = current_dir / "gdal"
    exe_file = current_dir / "GEHistoricalImagery.exe"
    resources_dir = current_dir / "resources"
    icon_file = resources_dir / "icon.ico"
    logo_file = resources_dir / "logo.ico"
    link_image = resources_dir / "link.jpg"
    
    # 检查必要文件是否存在
    required_files = [main_script, coord_convert, gdal_dir, exe_file, resources_dir]
    required_resource_files = [icon_file, logo_file, link_image]
    
    missing_files = [f for f in required_files if not f.exists()]
    missing_resource_files = [f for f in required_resource_files if not f.exists()]
    
    if missing_files:
        print("错误：以下必要文件或目录不存在：")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    if missing_resource_files:
        print("警告：以下资源文件不存在，但不影响打包：")
        for file in missing_resource_files:
            print(f"  - {file}")
    
    print("开始打包应用程序...")
    
    # 构建PyInstaller命令
    cmd = [
        "pyinstaller",
        "--onedir",  # 打包成文件夹
        "--windowed",  # 无控制台窗口
        "--name=小白影像下载器",  # 应用程序名称
        "--distpath=dist",  # 输出目录
        "--workpath=build",  # 工作目录
        "--specpath=.",  # spec文件位置
        f"--add-data={coord_convert};.",  # 添加坐标转换模块
        f"--add-data={gdal_dir};gdal",  # 添加GDAL目录
        f"--add-data={resources_dir};resources",  # 添加资源目录
        f"--add-binary={exe_file};.",  # 添加GEHistoricalImagery.exe
        "--hidden-import=coord_convert",  # 隐式导入
        "--hidden-import=folium",
        "--hidden-import=folium.plugins.draw",
        "--hidden-import=PyQt5.QtWebEngineWidgets",
        "--collect-all=folium",  # 收集folium所有文件
        "--collect-all=branca",  # folium依赖
        "--collect-all=jinja2",  # folium依赖
        "--clean",
        "--noconfirm",
        str(main_script)
    ]
    
    # 添加图标文件
    if icon_file.exists():
        cmd.insert(-1, f"--icon={icon_file}")
        print(f"使用图标文件: {icon_file}")
    elif logo_file.exists():
        cmd.insert(-1, f"--icon={logo_file}")
        print(f"使用备用图标文件: {logo_file}")
    else:
        print("警告: 未找到图标文件，将使用默认图标")
    
    try:
        # 执行打包命令
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=current_dir, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        
        print("PyInstaller打包完成!")
        
        # 检查输出目录
        dist_dir = current_dir / "dist" / "小白影像下载器"
        if dist_dir.exists():
            print(f"\n打包成功! 输出目录: {dist_dir}")
            print("\n打包内容:")
            for item in dist_dir.iterdir():
                print(f"  - {item.name}")
            
            # 创建启动脚本
            create_launcher_script(dist_dir)
            
            print("\n使用说明:")
            print(f"1. 进入目录: {dist_dir}")
            print("2. 双击运行: 小白影像下载器.exe")
            print("3. 或者双击运行: start.bat (如果exe无法运行)")
            
        else:
            print("错误: 打包输出目录不存在")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"打包过程中发生错误: {e}")
        return False
    
    return True

def create_launcher_script(dist_dir):
    """创建启动脚本"""
    launcher_script = dist_dir / "start.bat"
    script_content = '''@echo off
chcp 65001 > nul
echo 启动小白影像下载器...
"小白影像下载器.exe"
if errorlevel 1 (
    echo 程序运行出错，按任意键退出...
    pause > nul
)
'''
    
    try:
        with open(launcher_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"已创建启动脚本: {launcher_script}")
    except Exception as e:
        print(f"创建启动脚本失败: {e}")

def install_requirements():
    """安装必要的依赖包"""
    requirements = [
        "pyinstaller",
        "PyQt5",
        "folium",
        "branca",
        "jinja2"
    ]
    
    print("检查并安装必要的依赖包...")
    for package in requirements:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✓ {package}")
        except subprocess.CalledProcessError:
            print(f"✗ {package} 安装失败")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("小白影像下载器 - 打包工具")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        print("依赖安装失败，请手动安装后重试")
        sys.exit(1)
    
    # 执行打包
    if main():
        print("\n打包完成!")
    else:
        print("\n打包失败!")
        sys.exit(1)