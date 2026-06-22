# SPL_Meter
An SPL Meter running on Raspberry Pi

# apply the UI app
1(under \SPL_Meter)and install requirements

pip install -r requirements.txt

python -m streamlit run src/ui_app.py

run UI

streamlit run src/ui_app.py

2 if you have no streamlit

python -m streamlit run src/ui_app.py

2.1 No module named streamlit

python -m pip install streamlit

you will get"

      Welcome to Streamlit!

      If you'd like to receive helpful onboarding emails, news, offers, promotions,
      and the occasional swag, please enter your email address below. Otherwise,
      leave this field blank.

      Email:"
JUST ENTER

The ui use data from"input_device_index=0" 