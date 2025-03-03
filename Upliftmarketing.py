# -*- coding: utf-8 -*-
"""Assigment 34-UpliftMarketing-AfhiFadhlika

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1dDyp0dLlslNiAQTWplAodwl0uFl9ea7u

# Install, Load Packages
"""

!pip install causalml
!pip install scikit-plot

pip install -q ydata-profiling

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from ydata_profiling import ProfileReport

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, roc_auc_score, classification_report

import scikitplot as skplt

from sklearn.tree import DecisionTreeClassifier
from lightgbm import LGBMClassifier

from causalml.inference.meta import BaseSClassifier
from causalml.dataset import make_uplift_classification
from causalml.inference.tree import UpliftRandomForestClassifier
import causalml.metrics as metrics
from causalml.inference.tree import uplift_tree_string, uplift_tree_plot

from IPython.display import Image
plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["font.size"] = 25
sns.set()

"""# Load Dataset"""

raw_data = pd.read_csv("/content/data.csv")

raw_data

"""# Data Profiling"""

raw_data.info()

raw_data.describe()

"""# Data Exploration

## Numerical Variable Distribution
"""

#used_discount
sns.countplot(data = raw_data, x = 'used_discount')
plt.title('Discount Distribution')
plt.xlabel('Discount')
plt.ylabel('Frequency')
plt.show()

raw_data.used_discount.value_counts()

#used_bogo
sns.countplot(data = raw_data, x = 'used_bogo')
plt.title('Buy One Get One Distribution')
plt.xlabel('BOGO')
plt.ylabel('Frequency')
plt.show()

raw_data.used_bogo.value_counts()

#is_referral
sns.countplot(data = raw_data, x = 'is_referral')
plt.title('Referral Distribution')
plt.xlabel('Referral')
plt.ylabel('Frequency')
plt.show()

raw_data.is_referral.value_counts()

#conversion
sns.countplot(data = raw_data, x = 'conversion')
plt.title('Conversion Distribution')
plt.xlabel('Conversion')
plt.ylabel('Frequency')
plt.show()

raw_data.conversion.value_counts()

sns.countplot(data = raw_data, x = 'recency')
plt.title('Recency Distribution')
plt.xlabel('Recency')
plt.ylabel('Frequency')
plt.show()

raw_data.recency.value_counts()

"""## Categorical Variable Distribution"""

#zip_code
sns.countplot(data = raw_data, x = 'zip_code')
plt.title('Zip Code Distribution')
plt.xlabel('Zip Code')
plt.ylabel('Frequency')
plt.show()

raw_data.zip_code.value_counts()

#chanel
sns.countplot(data = raw_data, x = 'channel')
plt.title('Channel Distribution')
plt.xlabel('Channel')
plt.ylabel('Frequency')
plt.show()

raw_data.channel.value_counts()

sns.countplot(data = raw_data, x = 'offer');
plt.title('Offer Distribution')
plt.xlabel('Offer')
plt.ylabel('Frequency')
plt.show()

raw_data.offer.value_counts()

"""## Conversion Rate"""

conversion_rate_offer = raw_data.groupby('offer')['conversion'].mean()
conversion_rate_offer.plot(kind='bar')
plt.title('Conversion Rate by Offer')
plt.xlabel('Offer')
plt.ylabel('Conversion Rate')
plt.show()

conversion_rate_offer

conversion_rate_channel = raw_data.groupby('channel')['conversion'].mean()
conversion_rate_channel.plot(kind='bar')
plt.title('Conversion Rate by Channel')
plt.xlabel('Channel')
plt.ylabel('Conversion Rate')
plt.show()

conversion_rate_channel

conversion_rate_zip = raw_data.groupby('zip_code')['conversion'].mean()
conversion_rate_zip.plot(kind='bar')
plt.title('Conversion Rate by Zip Code')
plt.xlabel('Zip Code')
plt.ylabel('Conversion Rate')
plt.show()

conversion_rate_zip

"""# Data Preprocessing to Modeling"""

# treatment variable
treatment_variable = "offer"
# target variable
target_variable = "conversion"
# control category
control_category = "Buy One Get One"
# treatment category
treatment_category = "Discount"
# category to exclude if needed
exclusion_category = "No Offer"
# column to encode
categorical_columns = ["zip_code", "channel"]

"""## Remove Exclude Category"""

# Preprocessing
if exclusion_category != None:
  raw_data = raw_data.loc[raw_data[treatment_variable] != exclusion_category].reset_index(drop=True)

n_treatment = raw_data[treatment_variable].nunique()

n_treatment

sns.countplot(data = raw_data, x = treatment_variable);
plt.title('Offer Distribution')
plt.xlabel('Offer')
plt.ylabel('Frequency')
plt.show()

raw_data.offer.value_counts()

"""## Data Spliting"""

# Train-Test Split Data
X_train, X_test = train_test_split(
    raw_data,
    test_size = 0.5,
    random_state = 1000
)

X_train.head()

X_test.head()

X_train.offer.value_counts(normalize = True).plot.barh();

"""## One-hot Encoding"""

# Encode categorical variables on X train data
dummies = pd.get_dummies(X_train[categorical_columns])
X_train = pd.concat([X_train.drop(categorical_columns, axis=1), dummies], axis=1)

# Encode categorical variables on X test data
dummies = pd.get_dummies(X_test[categorical_columns])
X_test = pd.concat([X_test.drop(categorical_columns, axis=1), dummies], axis=1)

X_train.head()

X_test.head()

"""## Check Spending History by Experiment Group"""

is_treat = X_train[X_train.offer != control_category]
not_treat = X_train[X_train.offer == control_category]

is_treat.head()

# bins = 25
sns.distplot(is_treat.query("offer == 'Discount'").history, hist=True, kde=True, kde_kws={'linewidth': 4}, label='Discount')
sns.distplot(is_treat.query("offer == 'Buy One Get One'").history, hist=True, kde=True, kde_kws={'linewidth': 4}, label='Buy One Get One')
plt.legend(frameon=False, loc=0, ncol=1, prop={'size': 20});

"""## Check Recency Distribution by Experiment Group"""

# bins = 25
sns.distplot(is_treat.recency, hist=True, kde=True, kde_kws={'linewidth': 4}, label='treatment')
sns.distplot(not_treat.recency, hist=True, kde=True, kde_kws={'linewidth': 4}, label='control')
plt.legend(frameon=False, loc=0, ncol=1, prop={'size': 20});

"""# Develop Uplift Model"""

X_train.head()

x_col = X_train.drop([treatment_variable, target_variable], axis = 1).columns.tolist()
print(x_col)

"""## S-Learner

Define S-Learner (Classifier) using LGBMClassifier as base model
"""

slearner = BaseSClassifier(LGBMClassifier(), control_name=control_category)

"""**Estimate Average Treatment Effect**"""

slearner.estimate_ate(X_train[x_col].values, X_train[treatment_variable].values, X_train[target_variable].values, bootstrap_ci  = True)

"""**Predict CATE for Each Treatment**"""

slearner_tau = slearner.predict(X_test[x_col].values, X_test[treatment_variable].values, X_test[target_variable].values)

slearner_tau

"""**Insert result to dataframe**"""

X_test['s_learner_tau'] = slearner_tau

"""**Check uplift distribution**"""

sns.displot(data = X_test['s_learner_tau'])
plt.vlines([0], 0, 1400, linestyles = "dashed", colors = "red")
plt.xlabel('Uplift score')
plt.ylabel('Number of observations in validation set');

"""## Uplift-Tree (Uplift Random Forest)

Define uplift random forest classifier
"""

uplift_model = UpliftRandomForestClassifier(control_name=control_category, random_state=1000)

"""Fit model to data"""

uplift_model.fit(
    X_train[x_col].values,
    treatment = X_train[treatment_variable].values,
    y = X_train[target_variable].values
)

"""Do prediction with trained model"""

y_pred = uplift_model.predict(X_test[x_col].values, full_output=True)

"""Check the first 5 rows"""

y_pred.head()

X_test['uplift_forest_tau'] = uplift_model.predict(X_test[x_col].values, full_output=False)

X_test.head()

"""Check uplift distribution"""

sns.displot(data = X_test['uplift_forest_tau'])
plt.vlines([0], 0, 1400, linestyles = "dashed", colors = "red")
plt.title('Uplift Tree Distribution')
plt.xlabel('Uplift score')
plt.ylabel('Number of observations in validation set');

sns.displot(data = X_test['s_learner_tau'])
plt.vlines([0], 0, 1400, linestyles = "dashed", colors = "red")
plt.title('Uplift S-Learner Distribution')
plt.xlabel('Uplift score')
plt.ylabel('Number of observations in validation set');

"""## Model Evaluation"""

def auuc_metric_maker(dataframe, tau_outcome_var, control_category, treatment_category):

  treatment_category_result = X_test[[tau_outcome_var]].reset_index(drop=True)
  treatment_category_result.columns = [treatment_category]

  # If all deltas are negative, assing to control; otherwise assign to the treatment
  # with the highest delta
  best_treatment = np.where(
      (treatment_category_result < 0).all(axis=1),
      control_category,
      treatment_category_result.idxmax(axis=1)
  )
  # Create indicator variables for whether a unit happened to have the
  # recommended treatment or was in the control group
  actual_is_best = np.where(dataframe[treatment_variable] == best_treatment, 1, 0)
  actual_is_control = np.where(dataframe[treatment_variable] == control_category, 1, 0)

  synthetic = (actual_is_best == 1) | (actual_is_control == 1)
  synth = treatment_category_result[synthetic]

  auuc_score = (synth.assign(
      is_treated = 1 - actual_is_control[synthetic],
      conversion = dataframe.loc[synthetic, target_variable].values,
      model_result = synth.max(axis=1)
  ).drop(columns=list([treatment_category]))).rename(columns = {"model_result": tau_outcome_var})

  return auuc_score

"""### S-Learner Evaluation"""

slearner_auuc_score = auuc_metric_maker(X_test, tau_outcome_var = "s_learner_tau", control_category = control_category, treatment_category = treatment_category)

slearner_auuc_score.head()

print(slearner_auuc_score.columns)

"""Calculate treated group based who conversion our platform, treated or not"""

slearner_auuc_score.groupby('is_treated').sum()[[target_variable]]

"""### Uplift Forest Evaluation"""

uplift_forest_auuc_score = auuc_metric_maker(X_test, tau_outcome_var = "uplift_forest_tau", control_category = control_category, treatment_category = treatment_category)

uplift_forest_auuc_score.head()

"""## Cumulative Gain Plot

**S-Learner Model**
"""

metrics.plot_gain(slearner_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""**Uplift Forest Model**"""

metrics.plot_gain(uplift_forest_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""## AUUC and Qini Score

**AUUC for S-Learner**
"""

metrics.auuc_score(slearner_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""**AUUC for Uplift Forest**"""

metrics.auuc_score(uplift_forest_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""**Qini Score for S-Learner**"""

metrics.qini_score(slearner_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""**Qini Score for Uplift Forest**"""

metrics.qini_score(uplift_forest_auuc_score, outcome_col=target_variable, treatment_col='is_treated')

"""## Quantile Metrics

If the model is working well, we should see a larger positive difference in the highest decile, decreasing to a small or negative difference in the lowest decile (i.e. treatment rate similar to control rate, or lower than control rate). In other words, as predicted uplift increases, the true uplift from control to treatment group should increase as well.

**Create new dataframe object**
"""

X_test

def quantile_and_treatment(dataframe, tau_outcome_var, treatment_variable, control_category, treatment_category):
  # Bin uplift score by using quantile
  score_quantiles, score_quantile_bins = pd.qcut(
    x = dataframe[tau_outcome_var],
    q = 10,
    retbins = True,
    duplicates = 'drop'
  )
  dataframe['Quantile bin'] = score_quantiles
  # Calculate number of samples for each bins
  count_by_quantile_and_treatment = dataframe.groupby(['Quantile bin', treatment_variable])[treatment_variable].count().unstack(-1)
  return count_by_quantile_and_treatment[[control_category, treatment_category]]

final_result = quantile_and_treatment(X_test, tau_outcome_var = "uplift_forest_tau", treatment_variable = treatment_variable, control_category = control_category, treatment_category = treatment_category)

"""**Visualize the impact of the treatment**"""

final_result.plot.barh()
plt.xlabel('Number of observations');

"""## Uplift Quantile Chart"""

def true_uplift(dataframe, tau_outcome_var, target_variable, treatment_variable, treatment_category, ):
  # Bin uplift score by using quantile
  score_quantiles, score_quantile_bins = pd.qcut(
    x = dataframe[tau_outcome_var],
    q = 10,
    retbins = True,
    duplicates = 'drop'
  )

  dataframe['Quantile bin'] = score_quantiles
  # Get the conversion rates within uplift score quantiles for both groups
  validation_treatment_mask = dataframe[treatment_variable] == treatment_category
  treatment_by_quantile = dataframe[validation_treatment_mask]\
    .groupby('Quantile bin')[target_variable].mean()
  control_by_quantile = dataframe[~validation_treatment_mask]\
    .groupby('Quantile bin')[target_variable].mean()
  # calculate true uplift
  true_uplift_by_quantile = treatment_by_quantile - control_by_quantile
  return true_uplift_by_quantile

true_uplift_result = true_uplift(X_test, tau_outcome_var = "uplift_forest_tau", target_variable = target_variable, treatment_variable = treatment_variable, treatment_category = treatment_category)

true_uplift_result.head(5)

"""**Visualize uplift quantile chart**




"""

plt.rcParams["figure.figsize"] = (10, 8)
true_uplift_result.plot.barh()
plt.xlabel('True uplift');

"""The uplift quantile chart shows that, for the most part, true uplift increases from lower score bins to higher ones, which is what we’d expect to see if the model is working. So it appears our model can effectively segment out customers who more readily respond to treatment.

## Model Interpretation

### Feature Importance (Gain, Permutation, etc)
"""

slearner.plot_importance(X=X_test[x_col],
                        tau=X_test['s_learner_tau'],
                        method='auto',
                        random_state = 42,
                        features=x_col)

"""### Shapley Dependence Model

**Shap Value for History**
"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='history',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""**Shap Value for used_discount**"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='used_discount',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""**Shap Value for Recency**"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='recency',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""Shap Value for is_referral"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='is_referral',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""**Shap Value for zip_code_Rural**"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='zip_code_Rural',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""**Shap Value for used_bogo**"""

slearner.plot_shap_dependence(
    treatment_group=treatment_category,
    feature_idx='used_bogo',
    X=X_test[x_col].values,
    features = x_col,
    tau= X_test['s_learner_tau'],
    interaction_idx=None
)

"""## Special Explanation Method for Tree-Based Model

### Feature Importance
"""

pd.DataFrame(
    {
        "Variable": x_col,
        "Importance": uplift_model.feature_importances_
    }
).sort_values(by="Importance", ascending = True).plot(x = 'Variable', y = 'Importance', kind = 'barh');
