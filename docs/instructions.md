
### Чтобы обновить код и перезапустить контейнер

* останавливаем и удаляем текущий контейнер
```docker stop cryptopulsebot```
```docker rm cryptopulsebot```

* Меняем код

* Пересобираем контейнер
```docker build -t cryptopulsebot .```

* Перезапускам контейнер
```docker run -d --name cryptopulsebot -v cryptopulsebot_data:/app/data cryptopulsebot```

