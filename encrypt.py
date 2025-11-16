import hashlib
import hmac
import json
import base64
import time
from typing import Optional, Tuple


class ScoreEncryptor:
    """
    分数加密器，提供防篡改的分数加密和验证功能
    """

    def __init__(self, secret_key: str, salt: str = "greedy_snake_salt"):
        """
        初始化加密器

        Args:
            secret_key: 密钥，用于HMAC签名
            salt: 盐值，增加破解难度
        """
        self.secret_key = secret_key.encode('utf-8')
        self.salt = salt.encode('utf-8')

    def encrypt_score(self, score: int, is_auto: bool = False, timestamp: Optional[float] = None) -> str:
        """
        加密分数

        Args:
            score: 要加密的分数
            is_auto: 是否为自动模式
            timestamp: 时间戳，如果为None则使用当前时间

        Returns:
            加密后的字符串
        """
        if timestamp is None:
            timestamp = time.time()

        # 创建数据字典
        data = {
            'score': score,
            'is_auto': is_auto,  # 标记是否为自动模式
            'timestamp': timestamp,
            'salt': self.salt.decode('utf-8')
        }

        # 转换为JSON字符串
        json_str = json.dumps(data, sort_keys=True)  # 排序确保序列化一致性

        # 计算HMAC签名
        signature = self._calculate_hmac(json_str)

        # 组合数据和签名
        combined_data = {
            'data': data,
            'signature': signature
        }

        # 转换为JSON并Base64编码
        encrypted_json = json.dumps(combined_data, sort_keys=True)
        encrypted_score = base64.urlsafe_b64encode(encrypted_json.encode('utf-8')).decode('utf-8')

        return encrypted_score

    def decrypt_and_verify(self, encrypted_score: str, max_age: Optional[float] = None) -> Tuple[bool, int, bool]:
        """
        解密并验证分数

        Args:
            encrypted_score: 加密的分数字符串
            max_age: 最大允许的时间差（秒），None表示不检查时间

        Returns:
            (验证结果, 分数值, 是否为自动模式)
        """
        try:
            # Base64解码
            decoded_json = base64.urlsafe_b64decode(encrypted_score.encode('utf-8')).decode('utf-8')
            combined_data = json.loads(decoded_json)

            # 提取数据和签名
            data = combined_data['data']
            stored_signature = combined_data['signature']

            # 验证数据结构
            if 'score' not in data or 'timestamp' not in data or 'salt' not in data or 'is_auto' not in data:
                return False, 0, False

            # 验证盐值
            if data['salt'] != self.salt.decode('utf-8'):
                return False, 0, False

            # 验证时间戳（防止重放攻击）
            if max_age is not None:
                current_time = time.time()
                if current_time - data['timestamp'] > max_age:
                    return False, 0, False

            # 重新计算签名进行验证
            data_json = json.dumps(data, sort_keys=True)
            calculated_signature = self._calculate_hmac(data_json)

            # 使用恒定时间比较防止时序攻击
            if not hmac.compare_digest(stored_signature, calculated_signature):
                return False, 0, False

            # 验证通过，返回分数和模式
            return True, data['score'], data['is_auto']

        except (ValueError, KeyError, json.JSONDecodeError, base64.binascii.Error):
            # 任何解析错误都视为篡改
            return False, 0, False

    def _calculate_hmac(self, data: str) -> str:
        """
        计算数据的HMAC签名

        Args:
            data: 要签名的数据

        Returns:
            HMAC签名（十六进制字符串）
        """
        return hmac.new(
            self.secret_key,
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()


# 使用示例和工具函数
def create_default_encryptor():
    """
    创建默认的加密器实例
    """
    # 在实际应用中，这个密钥应该从安全的地方获取，而不是硬编码
    # 这里为了示例使用固定密钥，实际使用时应该使用更安全的方式
    secret_key = "THIS_CODE_IS_GENERATED_BY_DEEPSEEK"
    return ScoreEncryptor(secret_key)


# noinspection PyBroadException
def save_encrypted_score(score: int, is_auto: bool = False, filename: str = "score.dat"):
    """
    保存加密的分数到文件

    Args:
        score: 要保存的分数
        is_auto: 是否为自动模式
        filename: 文件名

    Returns:
        是否成功保存
    """
    encryptor = create_default_encryptor()
    encrypted = encryptor.encrypt_score(score, is_auto)

    with open(filename, 'w') as f:
        f.write(encrypted)


def load_and_verify_score(filename: str = "score.dat", max_age: float = 365 * 24 * 60 * 60) -> Tuple[bool, int, bool]:
    """
    从文件加载并验证分数

    Args:
        filename: 文件名
        max_age: 最大允许的文件年龄（秒），默认1年

    Returns:
        (验证结果, 分数值, 是否为自动模式)
    """
    try:
        with open(filename, 'r') as f:
            encrypted_score = f.read().strip()

        encryptor = create_default_encryptor()
        return encryptor.decrypt_and_verify(encrypted_score, max_age)
    except (FileNotFoundError, IOError, Exception):
        return False, 0, False


def update_high_score(new_score: int, is_auto: bool = False):
    """
    更新最高分（如果新分数更高且不是自动模式）

    Args:
        new_score: 新分数
        is_auto: 是否为自动模式

    Returns:
        是否更新成功
    """
    # 自动模式不记入最高分
    if is_auto:
        return False

    # 加载并验证当前最高分
    _, current_high_score, _ = load_and_verify_score()

    # 如果新分数更高，则更新
    if new_score > current_high_score:
        return save_encrypted_score(new_score, False)  # 明确标记为非自动模式

    return True


def get_high_score() -> int:
    """
    获取已验证的最高分（仅手动模式）

    Returns:
        最高分（如果验证失败返回0）
    """
    valid, score, is_auto = load_and_verify_score()

    # 只返回手动模式的最高分
    if valid and not is_auto:
        return score

    return 0


def get_all_scores() -> Tuple[int, int]:
    """
    获取手动和自动模式的最高分

    Returns:
        (手动模式最高分, 自动模式最高分)
    """
    valid, score, is_auto = load_and_verify_score()

    if valid:
        if is_auto:
            return 0, score  # 手动模式为0，自动模式为score
        else:
            return score, 0  # 手动模式为score，自动模式为0

    return 0, 0


# 在游戏中的使用示例
def handle_game_over(score: int, is_auto: bool):
    """
    处理游戏结束逻辑

    Args:
        score: 最终分数
        is_auto: 是否为自动模式
    """
    if is_auto:
        return
    update_high_score(score, False)

# 测试函数
def test_encryption():
    """测试加密解密功能"""
    encryptor = create_default_encryptor()

    # 测试手动模式
    score = 100
    encrypted = encryptor.encrypt_score(score, False)
    print(f"手动模式 - 原始分数: {score}")
    print(f"加密后: {encrypted}")

    # 验证手动模式
    valid, decrypted_score, is_auto = encryptor.decrypt_and_verify(encrypted)
    print(f"验证结果: {valid}, 解密分数: {decrypted_score}, 自动模式: {is_auto}")

    # 测试自动模式
    score_auto = 200
    encrypted_auto = encryptor.encrypt_score(score_auto, True)
    print(f"自动模式 - 原始分数: {score_auto}")
    print(f"加密后: {encrypted_auto}")

    # 验证自动模式
    valid, decrypted_score_auto, is_auto = encryptor.decrypt_and_verify(encrypted_auto)
    print(f"验证结果: {valid}, 解密分数: {decrypted_score_auto}, 自动模式: {is_auto}")

    # 测试篡改情况
    tampered = encrypted[:-5] + "xxxxx"  # 篡改最后几位
    valid, _, _ = encryptor.decrypt_and_verify(tampered)
    print(f"篡改后验证结果: {valid}")

    # 测试保存和加载
    save_encrypted_score(score, False)
    valid, loaded_score, is_auto = load_and_verify_score()
    print(f"文件加载验证: {valid}, 分数: {loaded_score}, 自动模式: {is_auto}")


if __name__ == "__main__":
    test_encryption()
    test_encryption()