"""
Main functon to kick off the machine learning analysis
"""
import pdb
import time
# import warnings
# import datetime as dt
# import matplotlib as mpl
# mpl.use('Agg')
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
# SVM = support vector machine, SVC = support vector classifier
from sklearn.svm import SVC

from utils.helper_funcs import timeme
from utils.db_utils import DBHelper
from utils.ml_utils import standardize, plot_decision_regions, IMG_PATH
from utils.data_utils import DAY_COUNTS, PER_SHARE, RETURNS, FWD_RETURNS, \
                             MARGINS, INDEX, RATIOS, OTHER
from research.ml_analysis.dev_work.knn import KNN
from research.ml_analysis.dev_work.dec_trees import DecisionTree, draw_tree
from research.ml_analysis.algorithms.adalinegd import AdalineGD
from research.ml_analysis.algorithms.adalinesgd import AdalineSGD
from research.ml_analysis.scripts.ml_algorithms import run_perceptron
from research.ml_analysis.scripts.model_evaluation import kfold_cross_validation
from research.ml_analysis.scripts.feature_selection import sbs_run, \
                                                           random_forest_feature_importance, \
                                                           logistic_regression_feature_importance, \
                                                           principal_component_analysis

FILE_PATH = '/home/ec2-user/environment/python_for_finance/data_grab/inputs/'
FILE_NAME = 'fmp_avail_stocks_20190619.txt'


def run(inputs, label='retfwd_2y', cust_ticks=None, test=False):
    """
    Main function to run analytics
    """
    if cust_ticks:
        tickers = cust_ticks
    else:
        tickers = list(pd.read_csv(FILE_PATH + FILE_NAME, header=None)[0].values)

    if test:
        tickers = tickers[:500]

    # Getting Dataframe
    time0 = time.time()
    with DBHelper() as dbh:
        dbh.connect()
        lis = ''
        for tick in tickers:
            lis += "'" + tick + "', "
        print("starting data retrieval")
        # removes data points that are unlabeled
        df_ret = dbh.select('fin_ratios', where='tick in (' + lis[:-2] + ')'
                            'and {} != 0'.format(label))
        # returns all data points even if labeled
        # df_ret = dbh.select('fin_ratios', where='tick in (' + lis[:-2] + ')')

    time1 = time.time()
    print("Done Retrieving data, took {0} seconds".format(time1-time0))

    # grab the more recent data for testing later
    # these wont have a target becuase the data is too recent
    if not test:
        test_df, train_df = separate_train_test(df_ret)
        # filtered_test_df = filter_live(test_df)
    else:
        train_df = df_ret
        # x_train, x_test, y_train, y_test = train_test_split(df_ret.drop(label, axis=1),
        #                                                     df_ret[label], test_size=0.1,
        #                                                     random_state=0)
        # train_df = pd.merge(x_train, y_train, right_index=True, left_index=True)
        # test_df = pd.merge(x_test, y_test, right_index=True, left_index=True)

    # clean data
    train_df = remove_unnecessary_columns(train_df)
    print("Number of rows in training set: {}".format(len(train_df)))
    train_df = clean_data(train_df)
    print("Number of rows in training set after cleaning: {}"
          "".format(len(train_df)))

    # Add the label column, set the index, and designate inputs for learning
    train_df = add_target(train_df, label, breaks=1)
    train_df = train_df.set_index(['tick', 'year', 'month'])
    train_df = select_inputs(train_df, inputs)
    # drop all rows with NA's
    size_before = len(train_df)
    train_df = train_df.dropna()
    print("There are {0} samples (removed {1} NA rows)"
          "".format(len(train_df), size_before - len(train_df)))

    # run data on custom algos
    custom_algos(train_df)

    # Select features
    # feature_selection(train_df, inputs)

    # Feature Extraction
    # feature_extraction(df, inputs)

    # Algorithms
    # timeme(run_perceptron)(train_df, tuple(inputs))
    # timeme(adalineGD)(train_df, tuple(inputs))
    # timeme(adalineSGD)(train_df, tuple(inputs))
    # timeme(run_perceptron_multi)(train_df, tuple(inputs))
    # model = timeme(logisticRegression)(train_df, tuple(inputs), C=100, penalty='l2')

    # model = timeme(k_nearest_neighbors)(df, tuple(inputs), k=8)
    # model = timeme(random_forest)(train_df, tuple(inputs), estimators=3)
    # model = timeme(support_vector_machines)(df, tuple(inputs), C=100)
    # timeme(nonlinear_svm)(df, tuple(inputs), C=1)
    # timeme(decision_tree)(df, tuple(inputs), md=4)
    # timeme(adalinesgd)(df, tuple(inputs), estimators=3)
    # timeme(run_perceptron_multi)(df, tuple(inputs), estimators=3)

    # Model Evaluation
    # model_evaluation(df, inputs)
    # timeme(majority_vote)(df, tuple(inputs))
    # timeme(bagging)(df, tuple(inputs))
    # timeme(adaboost)(df, tuple(inputs))
    # timeme(heat_map)(df, tuple(inputs))
    # timeme(linear_regressor)(df, tuple(inputs))
    # timeme(linear_regression_sklearn)(df, tuple(inputs))
    # timeme(ransac)(df, tuple(inputs))
    # timeme(polynomial_regression)(df, tuple(inputs))
    # timeme(nonlinear)(df, tuple(inputs))
    # timeme(random_forest_regression)(df, tuple(inputs))

    # test on recent data
    # preds = eval_on_curr_companies(model, filtered_cur_df, inputs)
    # pdb.set_trace()
    print()


def custom_algos(train):
    """
    Method to run on custom ML algorithms
    """
    cust_data = train.drop("target_proxy", axis=1).values
    # knn_inst = KNN(cust_data, cat=True)
    # print(knn_inst.run())
    # knn_inst.plot_knn(train.columns[0], train.columns[1])
    # knn_inst = KNN(cust_data, cat=True, opt=True)
    # knn_inst.plot_knn(train.columns[0], train.columns[1])
    tree = DecisionTree(data=cust_data)
    tree.prune(mingain=1.05)
    tree.print_tree()
    draw_tree(tree, jpeg='tree_cust_{}.jpg')
    pdb.set_trace()
    print()


def eval_on_curr_companies(model, data_df, inputs):
    pdb.set_trace()
    df_ind = data_df[['ticker', 'date', 'month']]
    df_trimmed = pd.DataFrame(standardize(data_df[inputs]), columns=inputs)
    df_combine = pd.concat([df_ind.reset_index(drop=True), df_trimmed], axis=1)
    predictions = {}
    for _, row in df_combine.iterrows():
        print(row['ticker'] + "   " + row['date'] + "   " + str(row['month']), end="")
        pred = model.predict(row[inputs])[0]
        try:
            predictions[pred].append(row['ticker'])
        except:
            predictions[pred] = [row['ticker']]
        print("    Class Prediction: " + str(pred))
    return predictions


def feature_selection(train_df, inputs):
    """
    Sequential Backward Selection - feature selection to see
    which are the most telling variable
    Default is K-means Clustering

    Feature selection: Select a subset of the existing
                       features without a transformation

    Use this to limit down the factors we learn on
    """
    ests = []
    ests.append([DecisionTreeClassifier(criterion='entropy', max_depth=3,
                                        random_state=0), 'DecTree'])
    ests.append([RandomForestClassifier(criterion='entropy', n_estimators=3,
                                        random_state=1, n_jobs=3), 'RandForest'])
    # ests.append([SVC(kernel='linear', C=100, random_state=0), 'SVC'])
    ests.append([LogisticRegression(C=100, random_state=0, penalty='l1'),
                 'LogRegr'])
    # ests.append([AdalineSGD(n_iter=15, eta=0.001, random_state=1),
    #              'AdalineSGD'])
    # ests.append([AdalineGD(n_iter=20, eta=0.001), 'AdalineGD'])
    ests.append([KNeighborsClassifier(n_neighbors=3), 'Kmeans'])

    ranks = []
    # for ind_est in ests:
    #     print("running for {}".format(ind_est[1]))
    #     ranks.append([ind_est[1], timeme(sbs_run)(train_df, tuple(inputs),
    #                                               est=ind_est[0], name=ind_est[1])])

    # Random Forest Feature Selection - using a random forest to identify
    # which factors decrease impurity the most
    pdb.set_trace()
    ranks.append([timeme(random_forest_feature_importance)(train_df,
                                                           tuple(inputs)), 'RandForestFeats'])

    # Logistic Regression Feature Selection - logistic regression
    # should expose the important variables through its weights
    pdb.set_trace()
    ranks.append([timeme(logistic_regression_feature_importance)(train_df,
                                                                 tuple(inputs)), "LogRegrWgts"])
    pdb.set_trace()
    for rank in ranks:
        print("Ranks for {}".format(rank[1]))
        print(rank[0])


def feature_extraction(data_df, inputs):
    """
    feature extraction --> Transform the existing features
                           into a lower dimensional space
    Transforms the data - can be used to linearly separate
                          data thru dimensionality reduction
    """
    timeme(principal_component_analysis)(data_df, tuple(inputs))
    # timeme(pca_scikit)(data_df, tuple(inputs))
    # timeme(linear_discriminant_analysis)(data_df, tuple(inputs))
    # timeme(lda_scikit)(data_df, tuple(inputs))


def model_evaluation(data_df, inputs):
    """
    Evaluate the performance of your model thru different techniques
    """
    timeme(kfold_cross_validation)(data_df, tuple(inputs))
    # timeme(learning_curves)(data_df, tuple(inputs))
    # timeme(validation_curves)(data_df, tuple(inputs))
    # timeme(grid_search_analysis)(data_df, tuple(inputs))
    # timeme(precision_vs_recall)(data_df, tuple(inputs))


def separate_train_test(data_df):
    """
    Separate the training and testing data
    """
    test_df = data_df[data_df.year == '2019']
    train_df = data_df[data_df.year != '2019']
    return test_df, train_df


def select_inputs(data_df, inputs):
    """
    Select the inputs to use for learning
    """
    columns = inputs + ['target'] + ['target_proxy']
    data_df = data_df[columns]
    return data_df


def add_target(data_df, tgt, breaks=2, custom_breaks=None):
    """
    Add the target column to be the label
    """
    num_of_breaks = breaks
    data_df['target_proxy'] = data_df[tgt]
    data_df = data_df.dropna(subset=['target_proxy'])
    data_df = data_df[data_df['target_proxy'] != 0]

    if not custom_breaks:
        break_arr = np.linspace(0, 100, num_of_breaks+2)[1:-1]
    else:
        break_arr = custom_breaks
    breaks = np.percentile(data_df['target_proxy'], break_arr)
    # breaks = np.percentile(data_df['target_proxy'], [50])
    data_df['target'] = data_df.apply(lambda x:
                                      target_to_cat_multi(x['target_proxy'], breaks), axis=1)
    return data_df


def target_to_cat_multi(proxy, breaks):
    """
    make the breaks between categories for a label
    """
    cat = 0
    for ind_b in breaks:
        if proxy < ind_b:
            return cat
        cat += 1
    return cat


def remove_unnecessary_columns(data_df):
    """
    Filter to only the columns we want
    """
    data_df = data_df[PER_SHARE + DAY_COUNTS + RETURNS + FWD_RETURNS + INDEX +
                      MARGINS + RATIOS + OTHER]
    return data_df


def filter_live(test_df):
    """
    Filter the live options by some boundary constraints
    """
    test_df = test_df[test_df['pe_ratio'] < 100]
    test_df = test_df[test_df['pe_ratio'] > 0]
    test_df = test_df[test_df['pb_ratio'] < 10]
    test_df = test_df[test_df['ps_ratio'] < 10]
    test_df = test_df[test_df['capex_to_rev'] < 100]
    return test_df


def clean_data(train_df):
    """
    Remove any outlier data
    """
    # To filter out errant data
    train_df = train_df[train_df['pe_ratio'] != 0]
    train_df = train_df[train_df['pb_ratio'] > 0]

    # To filter out outliers
    train_df = train_df[train_df['pe_ratio'] < 100]
    # train_df = train_df[train_df['capExToSales'] < 20]
    # train_df = train_df[abs(train_df['revenueGrowth']) < 200]
    # train_df = train_df[train_df['trailingPE'] > 0]
    # train_df = train_df[abs(train_df['sharpeRatio']) < 7]
    # train_df = train_df[train_df['sharpeRatio'] > 0]

    # Custom Filters for pruning
    # train_df = train_df[abs(train_df['trailingPE']) < 30]
    # train_df = train_df[abs(train_df['priceToBook']) < 10]
    # train_df = train_df[train_df['divYield'] > 0]
    # train_df = train_df[train_df['divYield'] < 8]
    # train_df = train_df[train_df['debtToEquity'] < 10]
    # train_df = train_df[train_df['returnOnEquity'] > 0]
    # train_df = train_df[train_df['returnOnEquity'] < 50]
    # train_df = train_df[train_df['currentRatio'] < 10]


    # only look at the top and bottom percentile ranges
    # train_df = train_df[(train_df['target'] == 0) | (train_df['target'] == 4)]
    return train_df


if __name__ == "__main__":
    # Most Relevant columns
    # COLS = ['roe', 'roa', 'pb_ratio', 'div_yield', 'ps_ratio',
    #         'pe_ratio', 'gross_prof_marg', 'net_prof_marg', 'peg_ratio',
    #         'ret_1y', 'ret_2y']
    COLS = ['pe_ratio', 'ret_on_cap']
    # TICKS = ['A', 'AAPL', 'AA', 'MSFT']

    run(COLS, test=True)
    # run(COLS)
    