import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
import seaborn as sns
import statsmodels.api as sm

# ---------- Custom Styling ----------
st.markdown(
    """
    <style>
        .stApp {
            background-color: #FFEB3B;  /* زرد روشن */
        }
        .stSidebar {
            background-color: #FFD700;  /* زرد طلایی */
        }
        .stButton>button {
            background-color: #FFF8E1;  /* زرد کرم برای دکمه‌ها */
            color: black;
        }
        .stTextInput>div>input {
            background-color: #FFF8E1;  /* زرد کرم برای فیلد ورودی */
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Header ----------
st.markdown(
    """
    <div style='display: flex; justify-content: center; align-items: center; flex-direction: column;'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/8/83/TUMS_Signature_Variation_1_BLUE.png' width='200' style='margin-bottom: 10px;'/>
    </div>
    """,
    unsafe_allow_html=True
)

st.title('🤖🤰 Machine Learning Models APP for Advanced Predicting Infertility Risk in Women')
st.info('Predict the **Infertility** based on health data using NNet and Logistic Regression.')

# ---------- Load Data ----------
@st.cache_data
def load_data():
    url = "https://github.com/Bahsobi/BRI_project/raw/refs/heads/main/selected_data.xlsx"
    return pd.read_excel(url)

df = load_data()

# ---------- Rename Columns ----------
df.rename(columns={
    'AGE': 'age',
    'Race': 'race',
    'Total Cholesterol': 'total_cholesterol',  # تغییر نام به total_cholesterol
    'Hyperlipidemia': 'hyperlipidemia',
    'diabetes': 'diabetes',
    'Female infertility': 'infertility',
    'BRI': 'BRI',  # استفاده از BRI
    'HOMA-IR': 'HOMA_IR',
    'Triglyceride': 'triglyceride'  # اضافه کردن Triglyceride
}, inplace=True)

# ---------- Features & Target ----------
features = ['BRI', 'age', 'total_cholesterol', 'HOMA_IR', 'race', 'hyperlipidemia', 'diabetes', 'triglyceride']  # اضافه کردن Triglyceride به فیچرها
target = 'infertility'
df = df[features + [target]].dropna()

X = df[features]
y = df[target]

# ---------- Preprocessing ----------
categorical_features = ['race', 'hyperlipidemia', 'diabetes']
numerical_features = ['BRI', 'age', 'total_cholesterol', 'HOMA_IR', 'triglyceride']  # اضافه کردن Triglyceride به ویژگی‌های عددی

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
    ('num', StandardScaler(), numerical_features)
])

# ---------- XGBoost Pipeline ----------
model = Pipeline([
    ('prep', preprocessor),
    ('xgb', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42))
])

X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
model.fit(X_train, y_train)

# ---------- Feature Importance ----------
xgb_model = model.named_steps['xgb']
encoder = model.named_steps['prep'].named_transformers_['cat']
feature_names = encoder.get_feature_names_out(categorical_features).tolist() + numerical_features
importances = xgb_model.feature_importances_
importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': importances
}).sort_values(by='Importance', ascending=False)

# ---------- Logistic Regression for Odds Ratio ----------
odds_pipeline = Pipeline([
    ('prep', preprocessor),
    ('logreg', LogisticRegression(max_iter=1000))
])
odds_pipeline.fit(X_train, y_train)
log_model = odds_pipeline.named_steps['logreg']
odds_ratios = np.exp(log_model.coef_[0])

odds_df = pd.DataFrame({
    'Feature': feature_names,
    'Odds Ratio': odds_ratios
}).sort_values(by='Odds Ratio', ascending=False)

filtered_odds_df = odds_df[~odds_df['Feature'].str.contains("race")]

# ---------- Sidebar User Input ----------
st.sidebar.header("📝 Input Individual Data")
race_options = [
    "Mexican American", "Other Hispanic", "Non-Hispanic White",
    "Non-Hispanic Black", "Non-Hispanic Asian", "Other Race - Including Multi-Racial"
]

# BRI: از ۱٫۳۱۲ تا ۲۲٫۹۸
BRI = st.sidebar.number_input("BRI (4 - 18)", min_value=1.312, max_value=22.98, value=5.88)

# سن: از ۱۸ تا ۵۹
age = st.sidebar.number_input("Age (18 - 45)", min_value=18, max_value=59, value=30)

# انتخاب نژاد
race = st.sidebar.selectbox("Race", race_options)

# کلسترول کل: از ۸۴ تا ۴۴۶
total_cholesterol = st.sidebar.number_input("Total Cholesterol (85 - 450)", min_value=84, max_value=446, value=185)

# تری گلیسرید: از ۱۰ تا ۸۷۶
triglyceride = st.sidebar.number_input("Triglyceride (30 - 360)", min_value=10, max_value=876, value=94)

# HOMA-IR: از ۰٫۲۲ تا ۴۲٫۲
HOMA_IR = st.sidebar.number_input("HOMA-IR (1 - 18)", min_value=0.22, max_value=42.2, value=3.83)



# هایپرلیپیدمی: بله یا خیر
hyperlipidemia = st.sidebar.selectbox("Hyperlipidemia", ['Yes', 'No'])

# دیابت: بله یا خیر
diabetes = st.sidebar.selectbox("Diabetes", ['Yes', 'No'])

# ---------- Prediction ----------
user_input = pd.DataFrame([{
    'BRI': BRI,
    'age': age,
    'total_cholesterol': total_cholesterol,  # تغییر به total_cholesterol
    'triglyceride': triglyceride,  # اضافه کردن Triglyceride
    'HOMA_IR': HOMA_IR,
    'race': race,
    'hyperlipidemia': hyperlipidemia,
    'diabetes': diabetes
}])

prediction = model.predict(user_input)[0]
probability = model.predict_proba(user_input)[0][1]
odds_value = probability / (1 - probability)

# ---------- Display Result ----------
if prediction == 1:
    st.error(f"""
        ⚠️ **Prediction: Infertile**

        🧮 **Probability of Infertility:** {probability:.2%}  
        🎲 **Odds of Infertility:** {odds_value:.2f}
    """)
else:
    st.success(f"""
        ✅ **Prediction: Not Infertile**

        🧮 **Probability of Infertility:** {probability:.2%}  
        🎲 **Odds of Infertility:** {odds_value:.2f}
    """)

# ---------- Show Tables ----------
st.subheader("📊 Odds Ratios for Infertility (Logistic Regression) (Excluding Race)")
st.dataframe(filtered_odds_df)

st.subheader("💡 Feature Importances (XGBoost)")
st.dataframe(importance_df)

# ---------- Plot Feature Importances ----------
st.subheader("📈 Bar Chart: Feature Importances")
fig, ax = plt.subplots()
sns.barplot(x='Importance', y='Feature', data=importance_df, ax=ax, color="#FF8C00")  # رنگ نارنجی کم رنگ
st.pyplot(fig)

# ---------- Quartile Odds Ratio for BRI ----------
st.subheader("📉 Odds Ratios for Infertility by BRI Quartiles")  # تغییر به BRI
df_bri = df[['BRI', 'infertility']].copy()  # تغییر به BRI
df_bri['BRI_quartile'] = pd.qcut(df_bri['BRI'], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])  # تغییر به BRI

X_q = pd.get_dummies(df_bri['BRI_quartile'], drop_first=True)  # تغییر به BRI
X_q = sm.add_constant(X_q).astype(float)
y_q = df_bri['infertility'].astype(float)

model_q = sm.Logit(y_q, X_q).fit(disp=False)
ors = np.exp(model_q.params)
ci = model_q.conf_int()
ci.columns = ['2.5%', '97.5%']
ci = np.exp(ci)

or_df = pd.DataFrame({
    'Quartile': ors.index,
    'Odds Ratio': ors.values,
    'CI Lower': ci['2.5%'],
    'CI Upper': ci['97.5%'],
    'p-value': model_q.pvalues
}).query("Quartile != 'const'")

st.dataframe(or_df.set_index('Quartile').style.format("{:.2f}"))

fig3, ax3 = plt.subplots()
sns.pointplot(data=or_df, x='Quartile', y='Odds Ratio', join=False, capsize=0.2, errwidth=1.5)
ax3.axhline(1, linestyle='--', color='gray')
ax3.set_title("Odds Ratios for Infertility by BRI Quartiles")  # تغییر به BRI
st.pyplot(fig3)

# ---------- Summary ----------
with st.expander("📋 Data Summary"):
    st.write(df.describe())

st.subheader("🎯 Infertility Distribution")
fig2, ax2 = plt.subplots()
df['infertility'].value_counts().plot.pie(
    autopct='%1.1f%%', labels=['Not Infertile', 'Infertile'], ax=ax2, colors=["#81c784", "#e57373"])
ax2.set_ylabel("")
st.pyplot(fig2)

with st.expander("🔍 Sample Data (First 10 Rows)"):
    st.dataframe(df.head(10))
