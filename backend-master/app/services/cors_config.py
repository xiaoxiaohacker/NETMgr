"""
CORS配置模块
用于配置跨域资源共享策略
"""

import os

# 生产环境应该配置具体的域名而不是使用通配符
# 示例配置：
# ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
#     "https://admin.your-domain.com",
# ]

# 从环境变量获取允许的源，如果没有则使用通配符（仅限开发环境）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]

# 生产环境中应该明确指定允许的方法和头部
ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH").split(",")
ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "X-Requested-With,content-type,Authorization,X-Client-Type").split(",")

# 在生产环境中禁用通配符的警告
if "*" in ALLOWED_ORIGINS:
    import warnings
    warnings.warn(
        "警告: 使用通配符 '*' 作为CORS来源是不安全的，仅应在开发环境中使用。"
        "在生产环境中，请设置ALLOWED_ORIGINS环境变量为具体的域名。",
        UserWarning
    )