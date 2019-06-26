# Udacity Full-Stack Nanodegree
# Item-Catalog (Fans store)
     A Fan store is a web application that providing fan categories and  each      category will have diffrent types of fans. integrate third party user registration and authentication.Registered users have the ability to add, modify, and   delete their own categories and items.

### Requirements of the project:
* Python3
* Vagrant 2.2.1
* VirtualBox 5.1.30
* Git 2.19.2
### Tips to Run Project:
  * ### Step-1
    * If you didn't installed python previously,than you can  Install python 3 , by refer [this](https://realpython.com/installing-python/)
       
    * If you didn't installed  Vagrant and VirtualBox softwares previously in your system.you can instal by clicking         [here](https://github.com/udacity/fullstack-nanodegree-vm)
    * download [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm)
    * In th vagrant folder, save the fanstore project. 
  * ### Step-2
    * Open git bash from the vagrant folder
    * Run the virtual-machine from vagrant by giving the command as ```vagrant up``` inside the  FSND-Virtual-Machine\vagrant
    * Login into the Linux VM with command as ```vagrant ssh.```If you need more about vagrant commands refer [here](https://www.vagrantup.com/docs/cli/)
    * After login to linux vm change to shared directory by giving command as ```cd /vagrant```
    * Now change directory to fanstore by command as ``` cd fanstore```
  * ### step-3
    * Now execute the fanStore project by running the command as ```python3 fanproject.py```
    * To view the project in the web browser, open http://localhost:5000 in your web browser like google chrome.
### JSON endpoints
Returns JSON of all fans
```http://localhost:5000/fans/all.json```
Returns JSON of particular category items.
```http://localhost:5000/fans/category/1.json``` 
