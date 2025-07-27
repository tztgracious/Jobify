#!/usr/bin/env python3
"""
测试API连接的简单脚本
"""
import requests
import os

def test_api_connection():
    """测试API连接"""
    base_url = "https://115.29.170.231"
    
    # 测试1: 检查API是否可访问
    print("🔍 测试1: 检查API可访问性")
    try:
        response = requests.get(f"{base_url}/api/v1/upload-resume/", timeout=10)
        print(f"✅ API可访问，状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ API不可访问: {e}")
        return False
    
    # 测试2: 上传简历文件
    print("\n📤 测试2: 上传简历文件")
    resume_path = "backend/test/fixtures/professional_resume.pdf"
    
    if not os.path.exists(resume_path):
        print(f"❌ 测试文件不存在: {resume_path}")
        return False
    
    try:
        with open(resume_path, 'rb') as f:
            files = {'file': ('test_resume.pdf', f, 'application/pdf')}
            response = requests.post(
                f"{base_url}/api/v1/upload-resume/",
                files=files,
                timeout=30
            )
        
        print(f"✅ 上传请求完成，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 上传成功！文档ID: {data.get('id')}")
            return True
        else:
            print(f"❌ 上传失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 上传过程中出错: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试API连接...")
    success = test_api_connection()
    if success:
        print("\n🎉 API连接测试成功！")
    else:
        print("\n💥 API连接测试失败！") 