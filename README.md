# movie_spider
爬取知乎某个问题下面的所有问题，并正则匹配获取关键数据，输出成txt，并输出词云图

#### 安装python3 用pip3 安装依赖

1.  apt-get install python3
2. apt-get install pip3
3. 安装requirements.txt中的依赖库 pip3 install xxxx

#### 使用方法

1. python3 login.py -g questionId ：这一步需要输入注册的电话号码和密码及验证码（服务器请拷贝出来查看）其他登录知乎登录方式请参考的[这个](https://github.com/zkqiang/Zhihu-Login)git地址

   `python login.py -g 31537241` 获取[你有哪些看过五遍以上的电影？](https://www.zhihu.com/question/31537241) 下面的回答形成zhihu.txt

   这个命令输出的数据是append方式，所以可以多个回答执行多次

2. python3 zhihu_login.py -o zhihu.txt   输出zhihu.txt 下以《》格式的词，我们统计次数并输出到out_movie.txt 并输出w.png 为词云图


<p align="center">
	<img src="https://github.com/linuxvae/movie_spider/blob/master/w.png?raw=true" alt="Sample"  width="450" height="450">
	<p align="center">
		<em>图片示例2</em>
	</p>


顺便我也通过爬虫，爬取了多个盗版视频网站的资源，并尝试用vue.js 写了一个web网站，比较粗糙，基本能用，上面获取爬取的电影，网站基本都有，网站只用于交流与学习，不用作商用 [电影网站](http://kanqiu.xyz/#/pc_movielist?id=1&type=0&flag=0&year=%E5%85%A8%E9%83%A8&flagtype=%E5%85%A8%E9%83%A8)

我把git获取的资源整合成了一个知乎专辑，部署在[知乎推荐top](http://kanqiu.xyz/#/pc_movielist?id=1&type=0&flag=3&year=%E5%85%A8%E9%83%A8&flagtype=%E5%85%A8%E9%83%A8)

到此获取完毕。
