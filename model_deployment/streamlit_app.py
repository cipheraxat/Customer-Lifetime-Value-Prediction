
#adding necessary libraries
import streamlit as st
import pandas as pd
import lifetimes
import math
import numpy as np
import xlrd
import datetime
np.random.seed(42)
import altair as alt
import time
import warnings
warnings.filterwarnings("ignore")
from math import sqrt
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from lifetimes.plotting import plot_frequency_recency_matrix
from lifetimes.plotting import plot_probability_alive_matrix
from lifetimes.plotting import plot_period_transactions
from lifetimes.utils import calibration_and_holdout_data
from lifetimes import ParetoNBDFitter
from lifetimes.plotting import plot_history_alive
from sklearn.metrics import mean_squared_error, r2_score

st.markdown(""" # Survival Analysis using CLV WebApp 👋


Upload the RFM(Recency, Frequency, and Monetary value) data and get your customer lifetime prediction on the fly !!! :smile:

	""")


st.image("https://www.singlegrain.com/wp-content/uploads/2020/01/calculation-for-customer-lifetime-value.jpg", use_column_width = True)


data = st.file_uploader("File Uploader")

st.sidebar.image("https://media-cldnry.s-nbcnews.com/image/upload/t_fit-2000w,f_auto,q_auto:best/newscms/2021_23/3481186/210608-doge-nft-2x1-cs.jpg", width = 250)
st.sidebar.markdown(""" **Made with :heart: by Akshat Anand** """)


st.sidebar.title("Input Features :pencil:")


st.sidebar.markdown("""

[Example CSV Input File](https://github.com/cipheraxat/Customer-Lifetime-Value-Prediction/blob/main/data%20files/sample_file.csv)

	""")

days = st.sidebar.slider("Select The No. Of Days", min_value = 1, max_value = 365, step = 1, value = 30)

profit = st.sidebar.slider("Select the Profit Margin", min_value = 0.01, max_value = 0.09, step = 0.01, value = 0.05)


t_days = days

profit_m = profit

slider_data = {
	"Days": t_days,
	"Profit": profit_m
}

st.sidebar.markdown("""

### Selected Input Features :page_with_curl:

	""")

features = pd.DataFrame(slider_data, index = [0])

st.sidebar.write(features)

st.sidebar.markdown("""

Before uploading the file, please select the input features first.

Also, please make sure the columns are in proper format. For reference you can download the [dummy data](https://drive.google.com/file/d/1MYsKxDrQpjEoPhSD7ucj3QiXHgJrer3o/view?usp=sharing).

**Note:** Only Use "CSV" File.

Wanna know what CLV is and why is it important for your business. 🤔 [Click here](https://piwik.pro/blog/customer-lifetime-value-important-for-your-business/)
	""")


if data is not None:

	def load_data(data, day = t_days, profit = profit_m):

		input_data = pd.read_csv(data)

		input_data = pd.DataFrame(input_data.iloc[:, 1:])

        #Pareto Model

		pareto_model = lifetimes.ParetoNBDFitter(penalizer_coef = 0.1)
		pareto_model.fit(input_data["frequency"],input_data["recency"],input_data["T"])
		input_data["p_not_alive"] = 1-pareto_model.conditional_probability_alive(input_data["frequency"], input_data["recency"], input_data["T"])
		input_data["p_alive"] = pareto_model.conditional_probability_alive(input_data["frequency"], input_data["recency"], input_data["T"])
		t = days
		input_data["predicted_purchases"] = pareto_model.conditional_expected_number_of_purchases_up_to_time(t, input_data["frequency"], input_data["recency"], input_data["T"])
        

        #Gamma Gamma Model

		idx = input_data[(input_data["frequency"] <= 0.0)]
		idx = idx.index
		input_data = input_data.drop(idx, axis = 0)
		m_idx = input_data[(input_data["monetary_value"] <= 0.0)].index
		input_data = input_data.drop(m_idx, axis = 0)


		input_data.reset_index().drop("index", axis = 1, inplace = True)

		ggf_model =  lifetimes.GammaGammaFitter(penalizer_coef=0.1)

		ggf_model.fit(input_data["frequency"], input_data["monetary_value"])

		input_data["expected_avg_sales_"] = ggf_model.conditional_expected_average_profit(input_data["frequency"], input_data["monetary_value"])

		input_data["predicted_clv"] = ggf_model.customer_lifetime_value(pareto_model, input_data["frequency"], input_data["recency"], input_data["T"], input_data["monetary_value"], time = 30, freq = 'D', discount_rate = 0.01)

		input_data["profit_margin"] = input_data["predicted_clv"]*profit

		input_data = input_data.reset_index().drop("index", axis = 1)

		#K-Means Model

		col = ["predicted_purchases", "expected_avg_sales_", "predicted_clv", "profit_margin"]

		new_df = input_data[col]

		k_model = KMeans(n_clusters = 4, init = "k-means++", n_jobs = -1, max_iter = 1000).fit(new_df)

		labels = k_model.labels_

		labels = pd.Series(labels, name = "Labels")

		input_data = pd.concat([input_data, labels], axis = 1)

		label_mapper = dict({0 : "Low", 3: "Medium", 1: "High", 2: "V_High"})

		input_data["Labels"] = input_data["Labels"].map(label_mapper)

		#saving the input data in the separate variable 

		download = input_data

		st.write(input_data)

		#adding a count bar chart

		fig = alt.Chart(input_data).mark_bar().encode(

			y = "Labels:N",
			x = "count(Labels):Q"

			)

		#adding a annotation to the chart

		text = fig.mark_text(

			align = "left",
			baseline = "middle",
			dx = 3

			).encode(

			text = "count(Labels):Q"

			)


		chart = (fig+text)

		#showing the chart

		st.altair_chart(chart, use_container_width = True)

		#creating a button to download the result

		if st.button("Download"):
			st.write("Successfully Downloaded!!! Please Check Your Default Download Location...:smile:" )
			return download.to_csv("customer_lifetime_prediction_result.csv")


	#calling the function		

	st.markdown("""

		## Customer Lifetime Prediction Result :bar_chart:

		""")

	load_data(data)

else:
	st.text("Please Upload the CSV File")
