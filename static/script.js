var QueryString = function () { //http://stackoverflow.com/questions/979975/how-to-get-the-value-from-the-url-parameter
  // This function is anonymous, is executed immediately and 
  // the return value is assigned to QueryString!
  var query_string = {};
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
        // If first entry with this name
    if (typeof query_string[pair[0]] === "undefined") {
      query_string[pair[0]] = pair[1];
        // If second entry with this name
    } else if (typeof query_string[pair[0]] === "string") {
      var arr = [ query_string[pair[0]], pair[1] ];
      query_string[pair[0]] = arr;
        // If third or later entry with this name
    } else {
      query_string[pair[0]].push(pair[1]);
    }
  } 
    return query_string;
} ();

var uribase="";

function PageScript(debug) {
	var self = this
	this.debug=debug

	PageScript.prototype.ajaxBase = function(callback) {
		var xmlhttp;
		if (window.XMLHttpRequest)
		  {// code for IE7+, Firefox, Chrome, Opera, Safari
		  xmlhttp=new XMLHttpRequest();
		  }
		else
		  {// code for IE6, IE5
		  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
		  }
		xmlhttp.onreadystatechange=function()
		  {
		  if (xmlhttp.readyState==4)
		    {
		    	callback(xmlhttp.status,xmlhttp.responseText,xmlhttp.responseXML);
		    }
		  }
		return xmlhttp;
	}

	PageScript.prototype.ajaxpost = function(uri,data,callback) {
		xmlhttp = this.ajaxBase(callback);
		xmlhttp.open("POST",uribase+uri,true);
		xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
		l = []
		for (key in data) {
			l.push(key +"=" +encodeURIComponent(data[key]));
		}
		t = l.join("&")
		console.log(t)
		xmlhttp.send(t);
	}

	PageScript.prototype.ajaxget = function(uri,callback) {
		xmlhttp = this.ajaxBase(callback)
		xmlhttp.open("GET",uribase+uri,true);
		xmlhttp.send();
	}

	PageScript.prototype.processErrors = function(data) {
			t = "<ul>"
			console.log(data)
			if (data.message) document.getElementById("message").innerHTML=data.message;
			if (data.assurances) document.getElementById("userdata").innerHTML=this.parse_userdata(data);
			errs = data.errors
			for ( err in errs ) t += "<li>"+ errs[err] +"</li>" ;
			t += "</ul>"
			document.getElementById("errorMsg").innerHTML=t
	}
	
	PageScript.prototype.parse_userdata = function(data) {
		userdata = "e-mail cím: "+data.email
		userdata +="<br>felhasználó azonosító: "+data.userid
		userdata +="<br>hash: "+data.hash
		userdata +="<br>biztosítási szintek:"
		userdata +="<ul>"
		for(ass in data.assurances) userdata += "<li>"+ass+"</li>"; 
		userdata +="</ul>"
		userdata +="<br>igazolások:"
		userdata +="<ul>"
		for(i in data.credentials) userdata += "<li>"+data.credentials[i].credentialType+"</li>" ;
		userdata +="</ul>"
		return userdata;		
	}

	PageScript.prototype.myCallback = function(status, text) {
		document.getElementById("errorMsg").innerHTML=text
		var data = JSON.parse(text);
		if (status == 200) {
			if(QueryString.next) {
				window.location = decodeURIComponent(QueryString.next)
			}
		}
		self.processErrors(data)
	}

	PageScript.prototype.passwordReset = function() {
	    secret = document.getElementById("PasswordResetForm_secret_input").value;
	    password = document.getElementById("PasswordResetForm_password_input").value;
	    this.ajaxpost("/v1/password_reset", {secret: secret, password: password}, this.myCallback)
	}
	
	PageScript.prototype.InitiatePasswordReset = function() {
		this.ajaxget("/v1/users/me", this.PWresetInitCallback)
	}

	PageScript.prototype.PWresetInitCallback = function(status, text){
		var data = JSON.parse(text);
		if (status == 200) {
			self.ajaxget("/v1/users/"+data.email+"/passwordreset", self.PWresetCallback)
		}
		else {
			document.getElementById("InitiatePasswordReset_ErrorMsg").innerHTML+="<p class='warning'>Nincs bejelentkezett felhasználó</p>";
		}
	}
	
	PageScript.prototype.PWresetCallback = function(status, text) {
		var data = JSON.parse(text);
		if (data.message) document.getElementById("InitiatePasswordReset_ErrorMsg").innerHTML+="<p class='warning'>"+data.message+"</p>";
	} 
	
	PageScript.prototype.login = function() {
	    username = document.getElementById("LoginForm_username_input").value;
	    var onerror=false;
		document.getElementById("LoginForm_errorMsg").innerHTML="";
		if (username=="") {
			document.getElementById("LoginForm_errorMsg").innerHTML+="<p class='warning'>A felhasználónév nincs megadva</p>";
			onerror=true;
		}
	    password = document.getElementById("LoginForm_password_input").value;
	    if (password=="") {
			document.getElementById("LoginForm_errorMsg").innerHTML+="<p class='warning'>A jelszó nincs megadva</p>";
			onerror=true; 
		}
		if (onerror==true) return;
		else {
			username = encodeURIComponent(username);	
			password = encodeURIComponent(password);
			this.ajaxpost("/login", {credentialType: "password", identifier: username, secret: password}, this.myCallback)
		}
	}

	PageScript.prototype.login_with_facebook = function(userId, accessToken) {
	    username = userId
	    password = encodeURIComponent(accessToken)
	    data = {
	    	credentialType: 'facebook',
	    	identifier: username,
	    	secret: password
	    }
	    this.ajaxpost("/login", data , this.myCallback)
	}

	PageScript.prototype.byEmail = function() {
	    email = document.getElementById("ByEmailForm_email_input").value;
	    email = encodeURIComponent(email)
	    this.ajaxget("/v1/user_by_email/"+email, this.myCallback)
	}

	PageScript.prototype.logoutCallback = function(status, text) {
		self.myCallback(status,text);
	    window.location = QueryString.uris.START_URL		
	}
	PageScript.prototype.logout = function() {
	    this.ajaxget("/logout", this.logoutCallback)
	}


	PageScript.prototype.uriCallback = function(status,text) {
		document.getElementById("errorMsg").innerHTML=text
		var data = JSON.parse(text);
		QueryString.uris = data
		self.processErrors(data)
		loc = '' + window.location
		if(loc.indexOf(QueryString.uris.SSL_LOGIN_BASE_URL) === 0) {
			console.log("ssl login");
			self.ajaxget(QueryString.uris.SSL_LOGIN_BASE_URL+'/ssl_login',pageScript.myCallback)
		}		
		
	}
	
	PageScript.prototype.sslLogin = function() {
		loc = '' +window.location
		newloc = loc.replace(QueryString.uris.BASE_URL, QueryString.uris.SSL_LOGIN_BASE_URL)
		console.log(newloc)
		window.location = newloc
	}

	PageScript.prototype.register = function() {
	    credentialType = document.getElementById("RegistrationForm_credentialType_input").value;
	    identifier = document.getElementById("RegistrationForm_identifier_input").value;
	    secret = document.getElementById("RegistrationForm_secret_input").value;
	    email = document.getElementById("RegistrationForm_email_input").value;
	    digest = document.getElementById("RegistrationForm_digest_input").value;
	    text= {
	    	credentialType: credentialType,
	    	identifier: identifier,
	    	secret: secret,
	    	email: email,
	    	digest: digest
	    }
	    this.ajaxpost("/v1/register", text, this.myCallback)
	}

	PageScript.prototype.register_with_facebook = function(userId, accessToken, email) {
	    username = userId;
	    password = accessToken;
	    text = {
	    	credentialType: "facebook",
	    	identifier: username,
	    	secret: password,
	    	email: email
	    }
	    this.ajaxpost("/v1/register", text, this.myCallback)
	}
	
	PageScript.prototype.getCookie = function(cname) {
	    var name = cname + "=";
	    var ca = document.cookie.split(';');
	    for(var i=0; i<ca.length; i++) {
	        var c = ca[i];
	        while (c.charAt(0)==' ') c = c.substring(1);
	        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
	    }
	    return "";
	} 
	
	PageScript.prototype.addAssurance = function() {
	    digest = document.getElementById("AddAssuranceForm_digest_input").value;
	    assurance = document.getElementById("AddAssuranceForm_assurance_input").value;
	    email = document.getElementById("AddAssuranceForm_email_input").value;
	    csrf_token = this.getCookie('csrf');
	    text= {
	    	digest: digest,
	    	assurance: assurance,
	    	email: email,
	    	csrf_token: csrf_token
	    }
	    this.ajaxpost("/v1/add_assurance", text, this.myCallback)
	}

	PageScript.prototype.hashCallback = function(status,text) {
		self.myCallback(status,text);
		self.ajaxget('/v1/users/me',self.myCallback);
	}

	PageScript.prototype.changeHash = function() {
	    digest = document.getElementById("ChangeHashForm_digest_input").value;
	    csrf_token = this.getCookie('csrf');
	    text= {
	    	digest: digest,
	    	csrf_token: csrf_token
	    }
	    self.ajaxpost("/v1/users/me/update_hash", text, this.hashCallback)
	}
	
	PageScript.prototype.digestGetter = function(formName) {
		self.formName = formName
		self.idCallback = function(status,text, xml) {
			if (status==200) {
		    	document.getElementById(self.formName + "_digest_input").value = xml.getElementsByTagName('hash')[0].childNodes[0].nodeValue;
				document.getElementById(self.formName + "_predigest_input").value = "";
				document.getElementById(self.formName + "_errorMsg").innerHTML="<p class='warning'>A titkosítás sikeres</p>"
			} else {
				document.getElementById(self.formName + "_errorMsg").innerHTML="<p class='warning'>" + text + "</p>"
			}
		}
	
		self.getDigest = function() {
			personalId = document.getElementById(this.formName+"_predigest_input").value;
			if ( personalId == "") {
				document.getElementById(self.formName + "_errorMsg").innerHTML="<p class='warning'>A személyi szám nincs megadva</p>"
				return;
			}
			text = "<id>"+personalId+"</id>"
			http = this.ajaxBase(this.idCallback);
			http.open("POST",'https://anchor.edemokraciagep.org/anchor',true);
			http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		  	http.setRequestHeader("Content-length", text.length);
		  	http.setRequestHeader("Connection", "close");
			http.send(text);
		}
		return self
	}

	PageScript.prototype.loadjs = function(src) {
	    var fileref=document.createElement('script')
	    fileref.setAttribute("type","text/javascript")
	    fileref.setAttribute("src", src)
	    document.getElementsByTagName("head")[0].appendChild(fileref)
	}
	
	PageScript.prototype.unittest = function() {
		this.loadjs("tests.js")
	}
	
	PageScript.prototype.meCallback = function(status, text) {
		if (status != 200) {
			document.getElementById("tab-login").checked = true;
		}
		else {
			document.getElementById("tab-account").checked = true; 
			var data = JSON.parse(text);
			if (data.assurances) {
				this.logged_in_user_Id=data.userid;
				document.getElementById("me_Msg").innerHTML=this.parse_userdata(data);
			}
		}
	}
	
	PageScript.prototype.deRegister = function() {
		if (document.getElementById("DeRegisterForm_password_input").value=="") {
			document.getElementById("DeRegisterForm_ErrorMsg").innerHTML="<p class='warning'>Nincs megadva a jelszó</p>";
			return;
		}
		else {
			self.ajaxget("/v1/users/me", function(status, text){
				if (status != 200) {
					document.getElementById("DeRegisterForm_ErrorMsg").innerHTML="<p class='warning'>Hibás autentikáció</p>";
					return;
				}
				else {
					var data = JSON.parse(text);
					text = {
						csrf_token: self.getCookie("csrf"),
						credentialType: "password",
						identifier: data.userid,
						secret: document.getElementById("DeRegisterForm_password_input").value
					}
					self.ajaxpost("/deregister", text, function(status, text){
						var data = JSON.parse(text);
						if (status != 200) document.getElementById("DeRegisterForm_ErrorMsg").innerHTML="<p class='warning'>"+data.errors+"</p>";
						else document.getElementById("DeRegisterForm_ErrorMsg").innerHTML="<p class='warning'>A fiók törlése megtörtént.</p>";
					})
				}
			})
		}
	}
	
	PageScript.prototype.main = function() {
		this.ajaxget("/uris", this.uriCallback)
		this.ajaxget("/v1/users/me", this.meCallback)
		if (QueryString.secret) {
			document.getElementById("PasswordResetForm_secret_input").value=QueryString.secret
			document.getElementById("tab-account").checked = true;
		}
		
	}

}

pageScript = new PageScript();
