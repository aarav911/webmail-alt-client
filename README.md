This is just a side project. 

I am build an alternative webmail clone for my university (IITB), for purely personal use. 

I do have some interesting ideas that i want to implement. 
1. Automatic notifications.
2. ML classicification for predicting whether an email is important for me or not. 


Right now the only way to access the client is by cloning this repo, making the venv (uv recommended), pip installing everything needed, and running `bash run.sh`. The script launches the current `app.py` source using the project venv when available, rather than an older executable in `dist/`.


Here is a screenshot of version, say 0.0.1
![A screenshot should be loaded here...](image.png)


## 📥 Download

Get the latest Windows executable here:  
[**Download Webmail.exe (v1.7)**](https://github.com/aarav911/webmail-alt-client/releases/download/v1.7/Webmail.exe)

*Requires Windows 10/11. No installation needed.*   

Note: You will need to put in your SSO TOKEN to login. [Get your SSO token following these steps.](https://www.cc.iitb.ac.in/attachments/ssoat/stepToReplacLDAPp-wWithSSOATforEmailClient.pdf)


---
## More screenshots
![alt text](image-1.png)
HTML rendering!!!

---
### Feature plan: 
In order of completion:
1. Wizard setup and in-app update
2. database caching and search
3. Pagination
4. background windows script notifications.

### Manual email-importance labels

Use **Mark Important** or **Mark Not Important** in the message viewer to add a
training example. Each click appends one JSON Lines record to
`imp_classification_model/manual_classification.jsonl` beside the app. Repeated
labels of the same message are retained as separate examples. The `raw_email`
field is Base64-encoded RFC822 data so the original server response can be
recovered without losing any bytes. The generated dataset is ignored by Git
because it contains private email content.