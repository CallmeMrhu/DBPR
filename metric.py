from sklearn.metrics import roc_auc_score as ras
import numpy as np
import pandas as pd
import heapq
import math


def AUC(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    auc = ras(y_true, y_pred)
    return auc


def currentDF(validationPath, timestep):
    timestamp = timestep * 30 * 24 * 3600
    df_validation = pd.read_csv(validationPath, sep='\t', header=None)
    if timestamp != 0:
        max_Timestamp = pd.Series.max(df_validation[3])
        min_Timestamp = pd.Series.min(df_validation[3])
        current_Timestamp = min_Timestamp + timestamp
        level_down_current = min_Timestamp
        level_up_current = current_Timestamp if current_Timestamp < max_Timestamp else max_Timestamp
        df_interval_current = df_validation[
            (df_validation[3] >= level_down_current) & (df_validation[3] < level_up_current)]
    else:
        df_interval_current = df_validation
    return df_interval_current


# ranking for every dataset and timestep
# Max = 100
def ranking(rootPath, testPath, timestep, itemMat, userMat, Max):
    itemMat = np.loadtxt(rootPath + 'evolution' + str(timestep) + '/' + itemMat + '.txt')
    userMat = np.loadtxt(rootPath + 'evolution' + str(timestep) + '/' + userMat + '.txt')
    df_interval_current = currentDF(testPath, timestep)
    userSet = list(df_interval_current[0].drop_duplicates())
    # 确定ranking.tsv文件的位置
    ranking_path = open(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', 'a')
    for userId in userSet:
        Pu = userMat[userId]
        result = dict()
        for i in range(len(itemMat)):
            Qi = itemMat[i]
            pro = np.dot(Pu, Qi)
            result[i] = pro
        # 取分数最高的前k个
        top_k_values = heapq.nlargest(Max, result.values())
        top_k_keys = list()
        for values in top_k_values:
            for keys in result.keys():
                if result[keys] == values:
                    top_k_keys.append(keys)
        # 保存至ranking.tsv文件中，方便以后直接对比，而不需要再进行矩阵运算
        for i in range(Max):
            result = str(userId) + '\t' + str(top_k_keys[i]) + '\t' + str(top_k_values[i]) + '\t' + str(0) + '\n'
            ranking_path.write(result)
    ranking_path.close()


def ranking_sparse(rootPath, trainPath, validationPath, testPath, timestep, itemMat, userMat, m, Max):
    # 先使用validation来做测试
    itemMat = np.loadtxt(rootPath + 'evolution' + str(timestep) + '/' + itemMat + '.txt')
    userMat = np.loadtxt(rootPath + 'evolution' + str(timestep) + '/' + userMat + '.txt')

    # df_interval_current = currentDF(validationPath, timestep)
    df_interval_current = currentDF(testPath, timestep)
    userSet = list(df_interval_current[0].drop_duplicates())
    # 确定ranking.tsv文件的位置
    ranking_path = open(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', 'a')
    # 获取train数据和validation中出现的item
    df_train = pd.read_csv(trainPath, header=None, sep='\t')
    df_validation = pd.read_csv(validationPath, header=None, sep='\t')
    # 之前为什么要才从1开始？
    all_itemset = set([n for n in range(0, m)])

    for userId in userSet:
        # 剔除掉train和validation中出现过的item
        df_train_itemset = set(df_train[df_train[0] == userId][1])
        df_validation_itemset = set(df_validation[df_validation[0] == userId][1])
        remain_itemset = all_itemset - df_train_itemset - df_validation_itemset

        Pu = userMat[userId]
        result = dict()
        for i in remain_itemset:
            Qi = itemMat[i]
            pro = np.dot(Pu, Qi)
            result[i] = pro
        # 取分数最高的前k个
        top_k_values = heapq.nlargest(Max, result.values())
        top_k_keys = list()
        for values in top_k_values:
            for keys in result.keys():
                if result[keys] == values:
                    top_k_keys.append(keys)
        # 保存至ranking.tsv文件中，方便以后直接对比，而不需要再进行矩阵运算
        for i in range(Max):
            result = str(userId) + '\t' + str(top_k_keys[i]) + '\t' + str(top_k_values[i]) + '\t' + str(0) + '\n'
            ranking_path.write(result)
    ranking_path.close()


def precision(rootPath, testPath, timestep, K, Max):
    df_interval_current = currentDF(testPath, timestep)
    df_ranking = pd.read_csv(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', header=None,
                             sep='\t')
    userSet = list(df_interval_current[0].drop_duplicates())
    precisionRate = 0
    for userId in userSet:
        df_current_user = df_interval_current[df_interval_current[0] == userId]
        df_interval_currentItem = set(df_current_user[1])
        # itemNum ????
        # 是记录条数，还是item的种类数字？？
        itemNum = len(df_interval_currentItem)
        # 需要判断当前用户打分项的类别数和所设置的K值大小，取较小的数
        # k = K if K < itemNum else itemNum
        k = K
        df_ranking_user = df_ranking[df_ranking[0] == userId].head(k)
        top_k_recommend = set(df_ranking_user[1])
        # 取交集，计算
        TP = len(df_interval_currentItem & top_k_recommend)
        precisionRate += float(TP) / float(k)
    precisionRate = precisionRate / len(userSet)
    return precisionRate


def reCall(rootPath, testPath, timestep, K, Max):
    df_interval_current = currentDF(testPath, timestep)
    df_ranking = pd.read_csv(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', header=None,
                             sep='\t')
    userSet = list(df_interval_current[0].drop_duplicates())
    recallRate = 0
    for userId in userSet:
        df_current_user = df_interval_current[df_interval_current[0] == userId]
        df_interval_currentItem = set(df_current_user[1])
        itemNum = len(df_interval_currentItem)
        df_ranking_user = df_ranking[df_ranking[0] == userId].head(K)
        top_k_recommend = set(df_ranking_user[1])
        # 取交集
        TP = len(df_interval_currentItem & top_k_recommend)
        recallRate += float(TP) / float(itemNum)
    recallRate = float(recallRate) / len(userSet)
    return recallRate


# Mean Reciprocal Rank
def MRR(rootPath, testPath, timestep, K, Max):
    df_interval_current = currentDF(testPath, timestep)
    df_ranking = pd.read_csv(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', header=None,
                             sep='\t')
    userSet = list(df_interval_current[0].drop_duplicates())
    MRR = 0
    for userId in userSet:
        df_current_user = df_interval_current[df_interval_current[0] == userId]
        df_interval_currentItem = set(df_current_user[1])
        # 是否需要判断当前用户打分的item类别数与K的大小？？？ 不需要
        # k = K if K < itemNum else itemNum
        df_ranking_user = df_ranking[df_ranking[0] == userId].head(K)
        # 注意要用list，因为set会自动排序，这样就打乱了推荐的顺序
        top_k_recommend = list(df_ranking_user[1])
        # num = 0
        MRR_rate = 0
        for key in top_k_recommend:
            if key in df_interval_currentItem:
                index = top_k_recommend.index(key)
                MRR_rate += 1.0 / (index + 1)
                # num += 1
        # if num != 0:
        #     MRR_rate = MRR_rate / num
        #     MRR += MRR_rate
        MRR += MRR_rate
    MRR = MRR / len(userSet)
    return MRR


def MAR(rootPath, testPath, timestep, K, Max):
    df_interval_current = currentDF(testPath, timestep)
    df_ranking = pd.read_csv(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', header=None,
                             sep='\t')
    userSet = list(df_interval_current[0].drop_duplicates())
    MAR = 0
    for userId in userSet:
        df_current_user = df_interval_current[df_interval_current[0] == userId]
        df_interval_currentItem = set(df_current_user[1])
        # due to be consistent with dPF, do not judge it
        # k = K if K < itemNum else itemNum
        df_ranking_user = df_ranking[df_ranking[0] == userId].head(K)
        # mush be list
        top_k_recommend = list(df_ranking_user[1])
        # num = 0
        MAR_rate = 0
        for key in top_k_recommend:
            if key in df_interval_currentItem:
                index = top_k_recommend.index(key)
                MAR_rate += (index + 1)
        MAR += MAR_rate
    MAR = MAR / len(userSet)
    return MAR


# in fact, we should metric all test items
def NGCG(rootPath, testPath, timestep, K, Max):
    df_interval_current = currentDF(testPath, timestep)
    df_ranking = pd.read_csv(rootPath + 'evolution' + str(timestep) + '/ranking' + str(Max) + '.tsv', header=None,
                             sep='\t')
    userSet = list(df_interval_current[0].drop_duplicates())
    NGCG = 0
    for userId in userSet:
        df_current_user = df_interval_current[df_interval_current[0] == userId]
        df_interval_currentItem = set(df_current_user[1])
        # 是否需要判断当前用户打分的item类别数与K的大小？？？ 不需要
        # k = K if K < itemNum else itemNum
        df_ranking_user = df_ranking[df_ranking[0] == userId].head(K)
        # 注意要用list，因为set会自动排序，这样就打乱了推荐的顺序
        top_k_recommend = list(df_ranking_user[1])
        NGCG_rate = 0
        for key in top_k_recommend:
            if key in df_interval_currentItem:
                index = top_k_recommend.index(key)
                NGCG_rate += 1.0 / math.log(index + 2)
        NGCG += NGCG_rate
    NGCG = NGCG / len(userSet)
    return NGCG
