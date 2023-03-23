import numpy as np
from statsmodels.stats import api as sms
import scipy.stats as st
import math
import pandas as pd


def sum_table(df_):

    """This function receives a dataset and returns a dataframe with information about each column of the dataset.
    Args:
        df_ (DataFrame): Dataset.

    Returns:
        DataFrame: returns a dataframe with the number of unique values and missing value of each column of a dataset.
    """

    summary = df_.dtypes.to_frame().rename(columns={0: 'dtypes'})
    summary['Uniques'] = df_.nunique()
    summary['Missing'] = df_.isnull().sum()
    summary['Missing %'] = np.round((df_.isnull().sum()/len(df_)).values*100, 2)
    summary = summary.reset_index().rename(columns={'index': 'Name'})

    return summary


def data(df):
    
    """This function receives a dataframe and devides it by device type and control and treatment group.

    Returns:
        Dict: A dictionary with 4 dataframes - the control e treatment group for each device.
    """

    df_site = df.query("device == 'I'")
    df_app = df.query("device == 'A'")

    df_site_a = df_site.query("group == 'GRP A'")
    df_site_b = df_site.query("group == 'GRP B'")

    df_app_a = df_app.query("group == 'GRP A'")
    df_app_b = df_app.query("group == 'GRP B'")

    return {'site_a':df_site_a, 'site_b':df_site_b, 'app_a':df_app_a, 'app_b':df_app_b}


def test_results(x_a, x_b, alpha, verbose=False):

    
    pvalue_a = st.shapiro(x_a)[1]
    pvalue_b = st.shapiro(x_b)[1]

    pa = pvalue_a > 0.05
    pb = pvalue_b > 0.05


    if (pa == True) & (pb == True):
        
        # Checking Homogeneity
        # Levene Test
        # H0: Equal variances.
        # H1: The variances are not equal.

        pvalue_var = st.levene(x_a, x_b)
        pvar = pvalue_var > 0.05

        if pvar == True:

            test_type ="Stundent's t-Test"
            stats, pvalue = st.ttest_ind(x_a, x_b, equal_var=True)
            #effect_size = sms.effectsize_smd(mean1=x_b.mean(), sd1=x_b.std(ddof=1), nobs1=len(x_b), mean2=x_a.mean(), sd2=x_a.std(ddof=1), nobs2=len(x_a))

        else:
            
            test_type = "Welch's t-Test"
            stats, pvalue = st.ttest_ind(x_a, x_b, equal_var=False)
            #effect_size = sms.effectsize_smd(mean1=x_b.mean(), sd1=x_b.std(ddof=1), nobs1=len(x_b), mean2=x_a.mean(), sd2=x_a.std(ddof=1), nobs2=len(x_a))
    else:

        test_type = "Mann Whitney U Test"
        stats, pvalue = st.mannwhitneyu(x_a, x_b)
      
    if pvalue < alpha:

        hypothesis = 'Rejeitar a hipótese nula.'
        comment = 'Há razões sufcientes para concluir que existe uma difirença estatisticamente siginificativa entre as médias no nível de significância 0.05.'

    else:

        hypothesis = 'Falha em rejeitar a hipótese nula.'
        comment = 'Não há evidências suficientes no nível de significância 0.05 para dizer que existe diferença entre as médias  dos grupos.'

    
    if verbose:

        print(test_type)
        print(f'\nP-value: {pvalue:.4f}')
        print(hypothesis)
        print(comment)

    else:

        return test_type, pvalue, hypothesis, comment 


# Sample Size
def sample_n(effect_size, power, alpha):
    
    """This function receives the effect size, statistical power and the significance level. Then it calculates the sample size needed to run the test. 
    """
    samp_n = sms.NormalIndPower().solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha
    )
    samp_n = math.ceil(samp_n)

    return samp_n


def tests(countries, metric, dataframes, sizes_dict_app, sizes_dict_site):

    results_site = pd.DataFrame()
    results_app = pd.DataFrame()

    for country in countries:

        dfs = data(dataframes[country])
        samp_size_site = sizes_dict_site[country]

        x_site_a = dfs['site_a'].sample(samp_size_site, random_state=0)[metric]
        x_site_b = dfs['site_b'].sample(samp_size_site, random_state=0)[metric]

        test_type_site, pvalue_site, hypothesis_site, comment_site  = test_results(x_site_a, x_site_b, alpha=0.05)

        test_result_site = {
                            'País': country,
                            'Dispositivo': 'Site',
                            'Teste': test_type_site,
                            'Hipótese': hypothesis_site, 
                            'p-value': pvalue_site,
                            'Comentário': comment_site 
                            }
    
        results_site = pd.concat([results_site, pd.Series(test_result_site)], axis=1)

        samp_size_app = sizes_dict_app[country]

            
        x_app_a = dfs['app_a'].sample(samp_size_app, random_state=0)[metric]
        x_app_b = dfs['app_b'].sample(samp_size_app, random_state=0)[metric]

        test_type_app, pvalue_app, hypothesis_app, comment_app  = test_results(x_app_a, x_app_b, alpha=0.05)

        test_result_app = {
                            'País': country,
                            'Dispositivo': 'App',
                            'Teste': test_type_app,
                            'Hipótese': hypothesis_app,
                            'p-value': pvalue_app, 
                            'Comentário': comment_app            
                           }
        results_app = pd.concat([results_app, pd.Series(test_result_app)], axis=1)

    return results_site, results_app 