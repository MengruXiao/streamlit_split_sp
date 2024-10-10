import streamlit as st
import re
import zipfile
import io
import tempfile
from pathlib import Path
import pandas as pd


def extract_procedure_name(sql):
    """从 SQL 语句中提取存储过程的名称"""
    match = re.search(r'CREATE OR REPLACE PROCEDURE\s+(\w+\.\w+)\(', sql, re.IGNORECASE)
    if match:
        full_name = match.group(1)
        _, sp_name = full_name.split('.')
        return sp_name
    return None


def extract_table_name(sql):
    """从 SQL 语句中提取表的名称"""
    match = re.search(r'CREATE TABLE IF NOT EXISTS\s+(\w+\.\w+)\s*', sql, re.IGNORECASE)
    if match:
        full_name = match.group(1)
        _, table_name = full_name.split('.')
        return table_name
    return None


def process_file(content):
    """处理文件内容，按 CREATE OR REPLACE PROCEDURE 分割"""
    # 按 "CREATE OR REPLACE PROCEDURE " 分割文本
    parts = content.split('CREATE OR REPLACE PROCEDURE ')

    # 去除空字符串
    procedures = [part.strip() for part in parts if part.strip()]

    # 合并分割后的部分，确保每个存储过程的 SQL 语句是完整的
    combined_procedures = []
    for proc in procedures:
        if proc:
            combined_procedures.append(f'CREATE OR REPLACE PROCEDURE {proc}')

    return combined_procedures


def process_file_view(content):
    """处理文件内容，按 CREATE OR REPLACE PROCEDURE 分割"""
    # 按 "CREATE OR REPLACE PROCEDURE " 分割文本
    parts = content.split('CREATE OR REPLACE VIEW ')

    # 去除空字符串
    procedures = [part.strip() for part in parts if part.strip()]

    # 合并分割后的部分，确保每个存储过程的 SQL 语句是完整的
    combined_procedures = []
    for proc in procedures:
        if proc:
            combined_procedures.append(f'CREATE OR REPLACE VIEW {proc}')

    return combined_procedures


def process_file_table(content):
    """处理文件内容，按 CREATE TABLE IF NOT EXISTS 分割"""
    # 按 "CREATE TABLE IF NOT EXISTS " 分割文本
    parts = content.split('CREATE TABLE IF NOT EXISTS ')

    # 去除空字符串
    tables = [part.strip() for part in parts if part.strip()]

    # 合并分割后的部分，确保每个表的 SQL 语句是完整的
    combined_tables = []
    for table in tables:
        if table:
            combined_tables.append(f'CREATE TABLE IF NOT EXISTS {table}')

    return combined_tables






def create_temp_file(temp_dir, filename, content):
    """将内容写入临时目录中的文件"""
    file_path = temp_dir / filename
    with file_path.open('w', encoding='utf-8') as file:
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


st.title('分割sp或view小工具')

# 选择功能
function = st.selectbox('选择功能', ['SP分割', 'view分割','table分割'])

# 允许用户上传一个 TXT 文件
uploaded_file = st.file_uploader('上传一个包含多个存储过程的 TXT或SQL文件', type=['txt','sql'])

schema = st.text_input('schema名', max_chars=100)

# 根据用户输入进行操作
st.write('schema名是', schema)

if st.button('处理并导出'):


    if uploaded_file:
        # 读取文件内容
        content = uploaded_file.read().decode('utf-8')

        if function == 'SP分割':
            # 处理文件内容
            procedures = process_file(content)

            # 创建一个临时目录来存储处理后的文件
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)

                # 生成命名规则为 sp名.sql 的文件
                for proc in procedures:
                    sp_name = extract_procedure_name(proc)
                    if sp_name:
                        filename = f"{schema}.{sp_name}.sql"
                        create_temp_file(temp_dir, filename, proc)
                        st.write(f"Created file: {filename}")
                    else:
                        st.write("Failed to extract procedure name from the following content:")
                        st.write(proc)

                # 创建 ZIP 文件
                zip_buffer = create_zip_file(temp_dir)

                # 提供下载链接
                st.download_button(
                    label="下载 ZIP 文件",
                    data=zip_buffer,
                    file_name="procedures.zip",
                    mime="application/zip"
                )
        elif function == 'view分割':

            # 处理文件内容
            procedures = process_file_view(content)

            # 创建一个临时目录来存储处理后的文件
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)

                # 生成命名规则为 sp名.sql 的文件
                for proc in procedures:
                    sp_name = extract_procedure_name(proc)
                    if sp_name:
                        filename = f"{schema}.{sp_name}.sql"
                        create_temp_file(temp_dir, filename, proc)
                        st.write(f"Created file: {filename}")
                    else:
                        st.write("Failed to extract procedure name from the following content:")
                        st.write(proc)

                # 创建 ZIP 文件
                zip_buffer = create_zip_file(temp_dir)

                # 提供下载链接
                st.download_button(
                    label="下载 ZIP 文件",
                    data=zip_buffer,
                    file_name="procedures.zip",
                    mime="application/zip"
                )

        elif function == 'table分割':

            # 处理文件内容
            procedures = process_file_table(content)

            # 创建一个临时目录来存储处理后的文件
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)

                # 生成命名规则为 sp名.sql 的文件
                filename_list=[]
                for proc in procedures:
                    sp_name = extract_table_name(proc)
                    if sp_name:
                        filename = f"{schema}.{sp_name}.sql"
                        create_temp_file(temp_dir, filename, proc)
                        filename_list.append(filename)
                        df = pd.DataFrame(filename_list, columns=['table_list'])
                        st.dataframe(df)
                        
                    else:
                        st.write("Failed to extract table  name from the following content:")
                        st.write(proc)
                        
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