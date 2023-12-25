import numpy as np


def armor_filter(armors):
    """
    装甲板去重
    :param armors:input np.ndarray (N,fp+conf+cls+img_no+bbox)
    :return: armors np.ndarray 每个id都最多有一个装甲板
    """
    # 直接取最高置信度
    ids = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12]  # 1-5分别为b1-5 8-12分别为r1-5
    if isinstance(armors, np.ndarray):
        results = []
        for i in ids:
            mask = armors[:, 9] == i
            armors_mask = armors[mask]
            if armors_mask.shape[0]:
                armor = armors_mask[np.argmax(armors_mask[:, 8])]
                results.append(armor)
        if len(results):
            armors = np.stack(results, axis=0)
            return armors
        else:
            return None
    else:
        return None

