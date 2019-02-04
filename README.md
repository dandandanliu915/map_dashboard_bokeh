# Map dashoboard implemented by Python module bokeh

I implemented a map dashboard with interactive filters in Python module bokeh. The original data source was from Burning Glass API. Building such visualizations of the raw data will make the life of data analytics eaiser. It also help other stakeholders to play around and gain insights. 

People will not prefer Python to do visualizations most of the time. If you're only familiar with modules such as matplotlib, it won't be able for you to realize much dashboard functionalities, especially interaction. Of course it will be much easier to build something simialr by Tableau, but usually such BI software licenses are not free. Besides, Python is such handy and concise language for students and professionals in data science field to process data. Why can't we just have a Python pipeline from raw data to BI? Well, here you go, bokeh. Bokeh is such a module it can create beautiful visualizations, and its galary impresses me every time. With a bit basic knowledge of javascript, one could easily make a fancy dashboard for free. 

Sample screen shot of phase 1 is as following:

![map-ScreenShot.png](map-ScreenShot.png)

The leftabove filter controls the bar plot and map plot. Each career area can be selected in the bar plot, its corresponding job posting count data will be shown on the map. And when multiple areas are selected, the map shows the accumulated data in each state. 

State name, count data and geo-coordinates can be found when hover over the map (countries except US will not show count data.) 

Deepest blue means the state is among the top 20% postings of all states. And the lightest blue shows the reversely.
