import base64

# 需要编码的字符串
original_string = "ak:sk"
# 将字符串编码为字节
bytes_string = original_string.encode("utf-8")
# 进行Base64编码
base64_encoded = base64.b64encode(bytes_string)

# 将字节转换为字符串
base64_string = base64_encoded.decode("utf-8")

print("Original String:", original_string)
print("Base64 Encoded String:", base64_string)