### OPEN.counter

lap | lap_soap_tired | STATE, JOKE | Отличная маскировка. Голый, в мыле и под юбкой тележки. Идем искать того, кто вырубил воду.
cap | none | PLOT | Гудение вентиляции вестибюля.

### OPEN.requests

iz | iz_formal | PLOT, CHAR | Заявка оформляется по форме: душевой комфорт.
ans | none | PLOT, JOKE | Ваша заявка принята, ожидайте.
iz | iz_formal | PLOT | Следующая заявка: textile care.
ans | none | PLOT, RHYTHM | Ваша заявка принята, ожидайте.

### OPEN.pa

pa | none | PLOT, CHAR | Уважаемые гости. Службы душевой комфорт, lobby water feature и textile care временно недоступны. Это плановые улучшения.

### OPEN.anc

anc | anc_calm | CHAR | Разведка тыла, потомок? Одобряю.
lap | lap_soap_worried | CHAR, JOKE | Главное, чтобы тыл не засветился перед гостями.

### Z04.look

lap | lap_soap_neutral | CLUE | Служебная изнанка стойки. Папка на мокром пятне, телефон, карта отеля и кнопка каскада. Ни одной ручки на ящиках.

### Z04.pump.look

lap | lap_soap_neutral | CLUE | Табличка «Lobby water feature: пуск».

### Z04.pump.use

cap | none | PLOT | Гудение насоса вхолостую. Загорается индикатор.
lap | lap_soap_neutral | CLUE, JOKE | Насос гудит, а каскад сухой. На камнях одна резкая сухая линия.

### Z04.pump.use.repeat

lap | lap_soap_tired | STATE | Всухую молотит.

### Z04.folder.look

lap | lap_soap_neutral | CLUE | Папка лежит ровно на мокром круге. След проступает по краям.

### Z04.folder.take

iz | iz_averted | CHAR, STATE | Документация стойки не подлежит перемещению.
lap | lap_soap_tired | CHAR, JOKE | Держит мертвой хваткой. Даже не глядя.

### Z04.map.look

lap | lap_soap_neutral | CLUE | Прозрачная карта отеля для гостей. Сквозь нее просвечивает столешница.

### Z04.map.take

lap | lap_soap_neutral | STATE, PLOT | Извлекается с изнанки. Пленка в мыльной руке держится.
iz | iz_averted | CHAR | Карты предназначены для визуального ознакомления.

### Z04.regulation.look

lap | lap_soap_neutral | CLUE | Ламинированный регламент пуска. Намертво привинчен к стойке. Между пунктами зачем-то аккуратно вырезано окно.

### Z04.regulation.take

lap | lap_soap_tired | STATE | Привинчено наглухо.

### Z04.drawer.look

lap | lap_soap_neutral | CLUE | Гладкие ящики без ручек по дизайн-коду.

### Z04.drawer.open

iz | iz_averted | CHAR, STATE | Личное имущество сотрудника досмотру не подлежит.
lap | lap_soap_neutral | STATE, JOKE | Задвинула ящик коленом. Не глядя.

### Z04.kefir.take

lap | lap_soap_tired | STATE | Скользкое стекло в мыльной руке не удержать.
iz | iz_averted | CHAR | Имущество не выдается.

### Z04.lowdrawer.open

cap | none | PLOT | Щелчок. Нижний ящик открывается нажатием.
lap | lap_soap_neutral | STATE, JOKE | Старая фарфоровая кефирная кружка. Переставлю-ка на столешницу тележки от греха подальше.
iz | iz_averted | CHAR | В нижнем отсеке хранение не предусмотрено.

### Z04.lowdrawer.again

lap | lap_soap_neutral | STATE | Пусто.

### TALK.req.early

lap | lap_soap_tired | STATE | Сначала надо самому проверить этот каскад и барабаны в прачечной.
iz | iz_formal | CHAR | Ожидайте.

### TALK.req.open

lap | lap_soap_neutral | CLUE | Три заявки на одно и то же?
iz | iz_formal | CHAR, STATE | Заявки оформляются по каждой услуге отдельно.
lap | lap_soap_tired | PLOT, CHAR | Каскад и барабаны целы.

### CHOICE.cause.three

choice | none | STATE | Три поломки.
lap | lap_soap_neutral | PLOT, CHAR | Каскад и прачечная целы. И всё встало в одну секунду — одна минута на всех табло прачечной.
iz | iz_formal | CHAR | Системы независимы.

### CHOICE.cause.empty

choice | none | STATE | Вода кончилась.
lap | lap_soap_neutral | PLOT | Кончалась бы — слабела бы, и на камнях была бы лесенка. А линия одна и резкая. Удар бывает от резкой остановки.
iz | iz_formal | CHAR | Снабжение бесперебойное.

### CHOICE.cause.cut

choice | none | STATE | Подачу перекрыли на общей линии.
lap | lap_soap_inspired | PLOT, CLUE | Гидроудар. Подачу резко перекрыли выше всех трех выходов. Одним движением.
cap | none | PLOT | Щелчок степлера. Ящик открывается коленом и закрывается.
iz | iz_formal | STATE | Документация оптимизирована.
lap | lap_soap_smug | CHAR, JOKE | Скрепила три бланка в один. А в ящике мелькнул кефир.

### TALK.req.again

iz | iz_formal | STATE | Заявка одна.

### W3.enter

lap | lap_soap_smug | STATE, CHAR | Гостей нет. Наконец-то можно вылезти из-под тележки и пройтись голышом. Ряды мертвых барабанов.

### W3.brand.look

lap | lap_soap_neutral | CLUE | Табличка на стене гордо гласит: Textile care.

### Z06.drums.look

cap | none | PLOT | Мигающие табло барабанов.
lap | lap_soap_neutral | CLUE, PLOT | На всех табло одна и та же оставшаяся минута. Сообщение: нет подачи воды.
lap | lap_soap_worried | CHAR, STATE | Люки заблокированы посреди цикла. Внутри вода, а за стеклом моя одежда.

### Z06.drum.restart

cap | none | PLOT | Писк. Сообщение «нет подачи воды» мигает.
lap | lap_soap_tired | STATE | Барабан глух к моим мольбам.

### Z06.hatch.open

lap | lap_soap_worried | STATE, CHAR | Заблокировано намертво посреди цикла. Внутри вода. Штаны так близко, но так недосягаемы.

### Z06.hatch.open.repeat

lap | lap_soap_tired | STATE | Замок не сдается.

### Z06.tank.probe

cap | none | PLOT | Всплеск стоячей воды. Пена ползет выше.
lap | lap_soap_panic | STATE, CHAR | Ептить! Любая порция жидкости раздувает эту пену. Шапка стала еще внушительнее.

### Z07.cladding.look

lap | lap_soap_neutral | CLUE | Декоративная стена. Гладкие бежевые панели без единой щели и ручек.

### Z07.cladding.use

lap | lap_soap_tired | STATE | Гладко, как моя репутация в этом отеле. Ухватиться не за что.

### Z08.cabinet.look

lap | lap_soap_neutral | CLUE | Старый советский металлический шкаф.

### Z08.cabinet.open

lap | lap_soap_neutral | CLUE, PLOT | На внутренней створке открытка «тов. К.» ко Дню работника ЖКХ от бригады профилактория.
lap | lap_soap_smug | STATE | В целлофане. Можно брать мыльными руками.

### Z08.cabinet.again

lap | lap_soap_neutral | STATE | Больше тут ловить нечего.

### W4.enter

lap | lap_soap_neutral | STATE, CHAR | Бывшая водолечебница, нынешний wellness-зал. Никого, голым тут можно.
lap | lap_soap_neutral | CLUE | Доска почета, архивный стол, люк старого источника под стеклом, wellness-стойка. И служебная дверь.

### W4.hatch.look

lap | lap_soap_neutral | CLUE | Люк старого источника под подсвеченным стеклом. Табличка heritage. Заложен намертво с дореволюционных времен, не передвинешь.

### W4.stairs.look

lap | lap_soap_neutral | CLUE | Обычная дверь. Надпись «Служебное помещение».

### W4.stairs.locked

lap | lap_soap_tired | STATE | Заперто.

### Z09.board.look

lap | lap_soap_neutral | CLUE, PLOT | Советские рамки. Среди них один свежий бежевый прямоугольник, из-под краски торчат шурупы таблички.
lap | lap_soap_neutral | STATE | Висит бумажка маляров «Осторожно, окрашено» и приколот акт приемки.

### Z09.paint.rub

lap | lap_soap_tired | STATE, JOKE | Краска мягкая, слой тонкий. Но мыльные пальцы просто размазывают бежевую грязь. Нужна жесткая кромка, которую мыло не размочит.

### Z09.paint.plunger

lap | lap_soap_tired | STATE | У резиновой присоски нет жесткой кромки.

### Z09.paint.token

lap | lap_soap_tired | STATE | Край жетона скруглен поколениями купальщиков. Не цепляет.

### Z09.paint.scrape

cap | none | PLOT | Скрежет ламината по краске.
lap | lap_soap_smug | CLUE, PLOT | Кромка ламината снимает бежевый слой ровными полосами. Открывается латунная табличка.
lap | lap_soap_neutral | CHAR, JOKE | Меню в бежевой краске. Этим самым приказом отель вычеркнул кефир.

### Z09.plate.look

lap | lap_soap_neutral | CLUE | Должность и инициал: «Старший по воде — тов. К.».

### Z09.slot.look

lap | lap_soap_neutral | CLUE | Латунная щель в стене. Надпись «Для жетоновъ» и заслонка.

### Z09.slot.use

cap | none | PLOT | Звон металла о пол.
lap | lap_soap_smug | STATE | Выпал застрявший жетон водолечебницы.

### Z10.table.look

lap | lap_soap_neutral | CLUE | Архивный стол. Тубус, папка профилактория, старый журнал и свежие распоряжения отеля.

### Z10.paper.take

lap | lap_soap_tired | STATE | Обычная бумага и старые документы раскиснут в моих мыльных руках. Читаем на месте.

### Z10.journal.read

lap | lap_soap_neutral | CLUE, PLOT | Старый журнал приёмки. В графе «Принялъ» напротив кефира стоят круглые лучистые оттиски. Все по четвергам.

### Z10.layoff.read

lap | lap_soap_neutral | CLUE, PLOT | Распоряжение управляющего. Сантехника сократили, а его функции никому не передали.

### Z10.memo.read

lap | lap_soap_neutral | CLUE | Советская памятка дежурной смене.

### Z10.tube.open

lap | lap_soap_neutral | CLUE, STATE | Восковка с планом 1908 года и фотография.
lap | lap_soap_smug | CHAR, PLOT | На фото та же латунная тележка на платформе. И пластина «Каскадъ».

### Z10.folder.open

lap | lap_soap_neutral | STATE, CLUE | Лекционная прозрачная пленка. Схема советского профилактория.

### Z10.films.lay

cap | none | PLOT | Шуршание пленок по стеклу светового стола.
lap | lap_soap_neutral | STATE, CLUE | Сложены по рамкам. Контуры здания совпали, но источник нарисован в трех разных местах.
lap | lap_soap_tired | CHAR, JOKE | А на карте отеля вообще нарисован купол, которого нет в природе.

### Z10.films.dome

lap | lap_soap_tired | STATE | Купола не существует. Карта отеля нарисована для красоты фасада.

### Z10.films.labels

lap | lap_soap_tired | STATE | Подписи не совпадают ни разу. Каждая эпоха переименовала всё по-своему.

### Z10.films.facade

lap | lap_soap_tired | STATE | Фасад на карте отеля симметризован для солидности. Контур врет.

### Z10.films.align

cap | none | PLOT | Пленки ложатся на подсвеченный люк. Доворот по номеру 317.
lap | lap_soap_inspired | CLUE, PLOT | Нарисованный источник на настоящий люк, водопровод на номер 317. Проступает одна вертикаль.
lap | lap_soap_smug | CHAR, JOKE | Источник, контора, док, шахта подъёмника... Wellness-стойка идеально ложится на грузовой подъёмникъ. Это всё одна труба.
lap | lap_soap_neutral | STATE | Противовес за стеной прачечной, стойка Изольды. И видна служебная лестница вниз.

### Z10.films.look

lap | lap_soap_neutral | STATE | Одна труба на три эпохи.

### Z10.films.elsewhere

lap | lap_soap_tired | STATE | Без настоящего люка под рукой совмещать не по чему.

### Z11.stand.look

lap | lap_soap_neutral | CLUE | Wellness-стойка. На опорах кто-то написал мелом «НАШЕ» и «НЕ ТРОГАТЬ».
lap | lap_soap_neutral | STATE | Поверх наклейки отеля «Не трогать — элемент дизайна». И закрашенная бежевая кнопка.

### Z11.stand.use

lap | lap_soap_tired | STATE | Стойка на чем-то жестко зажата. Не сдвинуть.

### W2.exhibit.look

lap | lap_soap_neutral | CLUE | Музейная витрина у каскада. Внутри контрольный счетчик водолечебницы. Табличка «Не трогать».

### SEQ.exhibit.go

cap | none | PLOT | Скрип колес. Тележка выезжает в вестибюль к экспонату.
lap | lap_soap_smug | STATE | Под прикрытием юбки. Изольда подняла доску, даже не глядя.

### SEQ.exhibit.nocover

lap | lap_soap_tired | STATE | Вестибюль людный. Человечество ещё не готово к встрече с голым Лапидусом. Только под тележкой.

### Z05.vitrine.look

lap | lap_soap_neutral | CLUE | Ни замочной скважины, ни ручки по дизайн-коду. Под кромкой резиновый упор защелки.
guest | none | CHAR | Тут написано — не трогать.

### Z05.vitrine.pry

lap | lap_soap_tired | STATE | Мыльные пальцы скользят. Щели нет.

### Z05.vitrine.plunger

lap | lap_soap_tired | STATE | Присоска держит стекло, но дверца не тянется на себя. Защелка открывается не так.

### Z05.vitrine.smash

lap | lap_soap_tired | STATE | Голый мыльный мужик и битое стекло посреди вестибюля. Нет.

### Z05.vitrine.push

cap | none | PLOT | Щелчок. Дверца отходит внутрь и распахивается.
guestf | none | CHAR | Женщина, вы читать умеете? Не трогать.
lap | lap_soap_smug | STATE, JOKE | Юбка распахнута ширмой. А дверца открывается нажатием — ровно тем, что запрещает табличка.

### Z05.meter.look

lap | lap_soap_neutral | CLUE | Счетчик стоит. А на корпусе свежая мокрая лучистая пломба.

### Z05.seal.wipe

lap | lap_soap_neutral | STATE | Чужую рабочую отметку инженер не стирает.

### Z05.seal.plunger.early

lap | lap_soap_neutral | STATE | Форма круглая, как у присоски моего вантуза. А вот лучи я уже где-то видел.

### Z05.seal.plunger

cap | none | PLOT | Влажный круг от вантуза ложится рядом с пломбой.
lap | lap_soap_inspired | CLUE, PLOT | Гладкий круг рядом с лучистым. Одна форма. Тот, кто принимал четверговые поставки в журнале, опломбировал общий счетчик.
lap | lap_soap_smug | CHAR | Круг под папкой Изольды на стойке — тот же знак.

### SEQ.exhibit.back

cap | none | PLOT | Скрип колес. Возврат за стойку.

### TALK.iz.open

iz | iz_averted | CHAR | У обслуживающего персонала есть вопросы по регламенту?
lap | lap_soap_neutral | STATE | Есть.

### TALK.iz.vitrine

choice | none | STATE | Попросить ключ от витрины экспоната.
iz | iz_formal | CHAR, CLUE | Витрина не запирается. Витрину не открывают.

### TALK.iz.stairs

choice | none | STATE | Дайте ключ от служебной лестницы.
iz | iz_formal | CHAR | Ключ выдаётся сантехнику. В настоящее время сантехник на аутсорсе.

### TALK.iz.seal

choice | none | STATE | Предъявить мокрую лучистую пломбу со счетчика.
iz | iz_formal | CHAR, CLUE | Сырость, протираем по графику.

### TALK.iz.plate

choice | none | STATE | Предъявить табличку «тов. К.» из-под краски.
iz | iz_formal | CHAR | Указанная табличка не соответствовала дизайн-коду.

### TALK.iz.signature

choice | none | STATE | Предъявить её подпись на акте малярной приёмки.
iz | iz_stern | CHAR, PLOT | Работы приняты в установленном порядке. Документация оформлена.
lap | lap_soap_tired | CHAR, JOKE | Фактов она не оспаривает. Она просто защищает себя казенными формулами.

### TALK.iz.signature.again

iz | iz_formal | STATE | Работы приняты.

### TALK.iz.kefir

choice | none | STATE | Спросить про кефир в ящике.
iz | iz_formal | CHAR | Личное имущество сотрудника.

### TALK.iz.model.early

choice | none | STATE | Изложить всё.
iz | iz_formal | CHAR | Нарушений в порядке не зафиксировано.
lap | lap_soap_tired | STATE | Мне не хватает какого-то документального факта.

### TALK.iz.layoff

choice | none | STATE | Сантехника сократили, его дело никому не передали.
lap | lap_soap_neutral | PLOT | Вы сократили сантехника.
iz | iz_flustered | CHAR, PLOT | Поставщик есть.
iz | iz_stern | CHAR, PLOT | Старый сантехник по четвергам носил вниз кефир и показания и здоровался.
iz | iz_formal | CHAR, PLOT | Новым сантехникам с аутсорса про четверги и доклад не передали.
lap | lap_soap_smug | CLUE, CHAR | Он всё подписывал мелом — «наше», «не трогать».

### TALK.iz.folder

cap | none | PLOT | Поднимает папку. Под ней мокрый круг.
iz | iz_tired | CLUE, PLOT | Уведомление пришло утром вместе с ударом.
lap | lap_soap_neutral | STATE | Подача приостановлена до выяснения. Под лучистой пломбой.

### TALK.iz.ladder

iz | iz_averted | CHAR | При покраске таблички только подержала стремянк, и всё.
lap | lap_soap_tired | CHAR, JOKE | Сводит свою роль к минимуму.

### TALK.iz.key

cap | none | PLOT | Ключ ложится на столешницу тележки.
iz | iz_averted | CHAR, PLOT | Дальнейшее выяснение вопроса передается в обслуживающий персонал.
lap | lap_soap_neutral | STATE | Главное, чтобы проблема уехала со стойки вниз.

### TALK.iz.after

iz | iz_formal | STATE | Всё сказано в установленном порядке.

### TALK.iz.exit

choice | none | STATE | Закончить разговор.
iz | iz_formal | CHAR | Ожидайте.

### SEQ.stairs.open

cap | none | PLOT | Щелчок замка, дверь открывается.
lap | lap_soap_neutral | STATE | Ключ остается в замке. Вниз ведет служебная лестница.

### W5.enter

lap | lap_soap_neutral | CLUE | Нижний предбанник. Сыро. Приемный док, латунные направляющие.
lap | lap_soap_worried | CHAR | Старые следы тележки. На стене инструкция. И массивная дверь конторы.

### Z12.dock.look

lap | lap_soap_neutral | CLUE | Пустой док. Направляющие в полу как раз под латунные башмаки старой тележки. Следы старые.

### Z12.instr.look

lap | lap_soap_neutral | STATE | Инструкция водолечебницы.

### Z12.door.look

lap | lap_soap_neutral | CLUE | Точно такое же влагостойкое уведомление, как под папкой на стойке.

### Z12.door.knock

cap | none | PLOT | Стук. Тишина.
lap | lap_soap_tired | STATE | Ни звука в ответ.

### Z12.door.use

lap | lap_soap_tired | STATE | Закрыто наглухо. Приём — в установленном порядке.

### Z12.seal.tear

lap | lap_soap_neutral | CHAR | Хороший инженер чужие пломбы не срывает.

### END.act2

lap | lap_soap_neutral | CLUE, PLOT | Итог: воду остановил старший по воде под зданием.
lap | lap_soap_tired | PLOT, CHAR | Ему перестали носить кефир и докладывать, а табличку тупо закрасили. Подношение это или оплата — пока не ясно.
lap | lap_soap_smug | CHAR, JOKE | Отличная ирония. Меня наградили путевкой, а этому работнику вообще не платят.
pa | none | CHAR | Плановые улучшения продолжаются.

### SEQ.w1.return

lap | lap_soap_tired | STATE | Обратно в 317-й.

### W1.shower.act2

lap | lap_soap_neutral | CLUE | Лейку вывернуло из держателя ударом. Сетка чистая, в трубе воздух.

### W2.cascade.look

lap | lap_soap_neutral | CLUE | Каскад абсолютно сух. И одна резкая сухая линия на камнях.

### W2.guests

guest | none | CHAR | Опять в лобби вайфай отваливается. Никакого сервиса за такие деньги.
guestf | none | CHAR | И кондиционер дует прямо в спину.

### W2.pa.more

pa | none | CHAR | Благодарим за понимание. Отель проводит плановые улучшения инфраструктуры.

### W2.getout

lap | lap_soap_tired | STATE | Людно. Вылезать из-под юбки сейчас — верный способ прославиться.

### HINT.done

anc | anc_calm | STATE | Тут всё, потомок.

### HINT.check.1

anc | anc_calm | CLUE | Прежде чем верить бланкам, проверь выходы воды сам.

### HINT.check.2

anc | anc_stern | CLUE | Каскад включается со стойки, прачечная — налево.

### HINT.check.3

anc | anc_smug | CLUE | Нажать кнопку каскада и осмотреть барабаны.

### HINT.cause.1

anc | anc_calm | CLUE | Сравни, когда встало.

### HINT.cause.2

anc | anc_stern | CLUE | Одна минута на всех табло и один удар.

### HINT.cause.3

anc | anc_smug | CLUE | Сказать Изольде: подачу перекрыли на общей линии.

### HINT.map.1

anc | anc_calm | CLUE | Ищи, где здание нарисовано.

### HINT.map.2

anc | anc_stern | CLUE | Прозрачная карта на стойке, планы на архивном столе.

### HINT.map.3

anc | anc_smug | CLUE | Взять карту из подставки и разложить все плёнки на стекле над люком.

### HINT.align.1

anc | anc_calm | CLUE | Три карты врут по-разному. Что не врёт?

### HINT.align.2

anc | anc_stern | CLUE | Источник не сдвинешь: он под стеклом.

### HINT.align.3

anc | anc_smug | CLUE | Наложить нарисованный источник на люк, довернуть по номеру 317.

### HINT.journal.1

anc | anc_calm | CLUE | Старые книги помнят, кто принимал.

### HINT.journal.2

anc | anc_stern | CLUE | Журнал на архивном столе.

### HINT.journal.3

anc | anc_smug | CLUE | Прочитать журнал приёмки.

### HINT.vitrine.1

anc | anc_calm | CLUE | Счётчик на общей линии — в вестибюле.

### HINT.vitrine.2

anc | anc_stern | CLUE | Ручек в этом отеле нет; как Изольда открывает ящик?

### HINT.vitrine.3

anc | anc_smug | CLUE | Подъехать под тележкой и нажать на стекло.

### HINT.seal.1

anc | anc_calm | CLUE | Знак на пломбе тебе знаком.

### HINT.seal.2

anc | anc_stern | CLUE | Круглый мокрый след — как от твоего вантуза.

### HINT.seal.3

anc | anc_smug | CLUE | Прижать вантуз рядом с пломбой.

### HINT.paint.1

anc | anc_calm | CLUE | Что прячет свежая краска на доске почёта?

### HINT.paint.2

anc | anc_stern | CLUE | Нужна жёсткая кромка, которую мыло не размочит.

### HINT.paint.3

anc | anc_smug | CLUE | Соскоблить краску ламинированным меню (оно в номере, если не взято).

### HINT.witness.1

anc | anc_calm | CLUE | Свидетель есть — за стойкой.

### HINT.witness.2

anc | anc_stern | CLUE | Обвинишь её — замолчит; дай ей виноватого на бумаге.

### HINT.witness.3

anc | anc_smug | CLUE | Прочитать распоряжение о сокращении и сказать ей: дело сантехника никому не передали.

### HINT.down.1

anc | anc_calm | CLUE | Ключ без двери — трофей без крепости.

### HINT.down.2

anc | anc_stern | CLUE | Служебная дверь в wellness-зале.

### HINT.down.3

anc | anc_smug | CLUE | Отпереть её и спуститься.

### DOC.notice_counter

```text
Увѣдомленіе
Подача приостановлена до выяснения
[оттиск]

```

### DOC.notice_door

```text
Увѣдомленіе
Подача приостановлена до выяснения
Приём — в установленном порядке
[оттиск]

```

### DOC.exhibit

```text
Экспонат. Контрольный счётчик водолечебницы «Каскадъ».
Оригинальная heritage-подача воды.
Не трогать
Ваш комфорт — наша концепция.
Управляющий

```

### DOC.journal

```text
Журналъ приёмки
4 апрѣля. Четвергъ. кефиръ 1 бут., доложено. Принялъ: [оттиск]
11 апрѣля. Четвергъ. кефиръ 1 бут., доложено. Принялъ: [оттиск]
18 апрѣля. Четвергъ. кефиръ 1 бут., доложено. Принялъ: [оттиск]
25 апрѣля. Четвергъ. кефиръ 1 бут., доложено. Принялъ: [оттиск]

```

### DOC.paint_act

```text
Акт малярной приёмки № 14
Окраска стены у доски почета в цвет дизайн-кода.
В перечне скрытых дефектов: табличка — 1 шт.
Принято: И. Т.

```

### DOC.layoff

```text
Распоряжение
В связи с отказом от избыточных ритуалов должность сантехника сократить.
Обязанности аутсорсу не передавать.
Ваш комфорт — наша концепция.
Управляющий

```

### DOC.plate_k

```text
Старший по воде — тов. К.

```

### DOC.regulation

```text
Регламент пуска
1. Проверить уровень.
[вырезано]
2. Нажать пуск.
*Непрофильные действия сокращены.
Ваш комфорт — наша концепция.
Управляющий

```

### DOC.memo

```text
Памятка дежурной смене
Перед пуском уведомить ответственное лицо.
Кефир выдавать строго по норме.
Профком.

```

### DOC.instr1908

```text
Инструкція
1. Проверить исправность направляющихъ.
2. Передъ пускомъ — доложиться старшему по водѣ.
3. По четвергамъ спускать кефиръ 1 бут. на телѣжкѣ.

```

### DOC.map_hotel

```text
Карта отеля
Wellness-стойка
Декоративная стена
Служебное помещение
Техническое помещение
Купол

```

### DOC.map_1908

```text
Планъ водолечебницы
Грузовой подъёмникъ
Пріёмный докъ
Контора старшаго по водѣ
Ванная № 17
Источникъ

```

### DOC.map_soviet

```text
Схема профилактория
Противовес
Прачечная
Палата 317
Грузовой лифт
Источник

```

### DOC.photo

```text
Четвергъ

```

### DOC.postcard

```text
Дорогой тов. К.!
С Днём работника ЖКХ!
От бригады профилактория.

```

### DOC.token

```text
На одно погруженiе

```

### INV.map.look

lap | lap_soap_neutral | CLUE | Прозрачная пленка карты отеля. В руках держится.

### INV.menu.painted

lap | lap_soap_neutral | CLUE | Ламинат в бежевых полосах после соскабливания краски.

### INV.key.look

lap | lap_soap_neutral | CLUE | Тяжелый ключ от служебной лестницы.

### INV.token.look

lap | lap_soap_neutral | CLUE | Латунь. Надпись: На одно погруженiе.

### INV.postcard.look

lap | lap_soap_neutral | CLUE | Открытка в плотном целлофане. Мыло ей не страшно.

### FB.films.1

lap | lap_soap_tired | STATE | Пленка прозрачная, но здесь её не к чему приложить.

### FB.films.2

lap | lap_soap_tired | STATE | Светить тут не на что, совмещать не с чем.

### FB.key.1

lap | lap_soap_tired | STATE | Не тот замок. Ключ не идет.

### FB.paper.1

lap | lap_soap_tired | STATE | Раскиснет в мыльных руках. Читаем на месте.

### FB.plunger.act2

lap | lap_soap_tired | STATE | Присоска держит, но тут держать нечего.

КОНЕЦ АКТА II
