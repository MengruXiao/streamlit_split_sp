import streamlit as st
import re
import zipfile
import io
import tempfile
from pathlib import Path


def extract_procedure_name(sql):
    """从 SQL 语句中提取存储过程的名称和 schema 名"""
    match = re.search(r'CREATE OR REPLACE PROCEDURE (\w+\.\w+)\(', sql, re.IGNORECASE)
    if match:
        full_name = match.group(1)
        schema, sp_name = full_name.split('.')
        return schema, sp_name
    return None, None


def process_file(content):
    """处理文件内容，按 CREATE OR REPLACE PROCEDURE 分割"""
    procedures = re.split(r'(CREATE OR REPLACE PROCEDURE)', content, flags=re.IGNORECASE)
    # 去除空字符串
    procedures = [proc.strip() for proc in procedures if proc.strip()]

    # 合并分割后的部分
    combined_procedures = []
    i = 0
    while i < len(procedures):
        if procedures[i].upper() == 'CREATE OR REPLACE PROCEDURE':
            combined_procedures.append(procedures[i] + procedures[i + 1])
            i += 2
        else:
            combined_procedures[-1] += procedures[i]
            i += 1

    return combined_procedures


def create_temp_file(temp_dir, filename, content):
    """将内容写入临时目录中的文件"""
    file_path = temp_dir / filename
    with file_path.open('w') as file:
        file.write(content)
    return file_path


def create_zip_file(temp_dir):
    """创建并返回一个包含临时目录中所有文件的 ZIP 文件对象"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for file_path in temp_dir.glob('*.sql'):
            zipf.write(file_path, arcname=file_path.name)
    zip_buffer.seek(0)
    return zip_buffer


st.title('sp或view分割')

# 允许用户上传一个 TXT 文件
uploaded_file = st.file_uploader('上传一个包含多个存储过程的 TXT 文件', type=['txt'])

if st.button('处理并导出'):
    if uploaded_file:
        # 读取文件内容
        content = uploaded_file.read().decode('utf-8')

        # 处理文件内容
        procedures = process_file(content)

        # 创建一个临时目录来存储处理后的文件
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)

            # 生成命名规则为 schema名.sp名.sql 的文件
            for proc in procedures:
                schema, sp_name = extract_procedure_name(proc)
                if schema and sp_name:
                    filename = f"{schema}.{sp_name}.sql"
                    create_temp_file(temp_dir, filename, proc)

            # 创建 ZIP 文件
            zip_buffer = create_zip_file(temp_dir)

            # 提供下载链接
            st.download_button(
                label="下载 ZIP 文件",
                data=zip_buffer,
                file_name="procedures.zip",
                mime="application/zip"
            )
    else:
        st.warning('请先上传一个 TXT 文件')