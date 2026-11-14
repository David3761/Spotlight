"""Turns check results into chapters: Romanian problem cards with fixes, solved items and checks that couldn't run."""

from typing import Literal

from pydantic import BaseModel

from app.models import (
    Business,
    Chapter,
    ChapterId,
    FixPanel,
    FixPayload,
    Problem,
    SolvedItem,
    UnknownItem,
)
from app.pipeline.romanian import TYPE_NOUNS
from app.pipeline.scoring import (
    CHAPTER_WEIGHTS,
    get_catalog_entry,
    get_chapter_score,
    get_problem_points,
)
from app.pipeline.types import CheckResult

LinkKind = Literal["google", "website", "instagram", "tiktok"]
"""Where a problem's deep link opens."""

DEV_STEPS = ["Trimite instrucțiunile persoanei care îți face site-ul."]
"""The steps of every problem fixed by the web developer."""

DIFFERENT_DATA_WHY = "Când datele diferă, Gemini nu știe pe care să le creadă și te recomandă mai rar."
"""Why a listing that disagrees with Google matters."""


class CheckTemplate(BaseModel):
    """The Romanian texts of one check; `{…}` placeholders take the check's params and the business context."""

    label_ro: str
    title_ro: str
    solved_ro: str
    why_ro: str
    steps_ro: list[str]
    evidence_ro: str | None = None
    where_ro: str | None = None
    max_chars: int | None = None
    link: LinkKind | None = None


class ChapterTexts(BaseModel):
    """The texts of a chapter page."""

    name_ro: str
    intro_ro: str
    where_to_fix_ro: str | None


CHAPTER_TEXTS: dict[ChapterId, ChapterTexts] = {
    "profil": ChapterTexts(
        name_ro="Profilul Google",
        intro_ro="Profilul tău Google e primul loc unde se uită Gemini când cineva caută o {type_noun} în {neighborhood}. "
        "Cu cât e mai complet, cu atât ai mai multe șanse să fii recomandat.",
        where_to_fix_ro="Aproape totul se face din aplicația Google Maps, din contul cu care ți-ai creat profilul. "
        "La fiecare problemă îți arătăm exact unde să apeși.",
    ),
    "recenzii": ChapterTexts(
        name_ro="Recenzii",
        intro_ro="Gemini citește recenziile ca să afle ce cred clienții despre tine. "
        "Contează câte ai, cât de noi sunt și dacă le răspunzi.",
        where_to_fix_ro="Din aplicația Google Maps, din contul cu care ți-ai creat profilul: acolo vezi recenziile și le poți răspunde.",
    ),
    "continut": ChapterTexts(
        name_ro="Conținutul site-ului",
        intro_ro="Gemini citește site-ul ca să afle ce oferi, unde ești și când ești deschis. "
        "Cu cât scrie mai clar, cu atât te poate recomanda mai ușor.",
        where_to_fix_ro="Pe site-ul tău. Îți scriem noi textele, iar tu sau persoana care îți face site-ul le pune pe pagină.",
    ),
    "site": ChapterTexts(
        name_ro="Site-ul, văzut de Gemini",
        intro_ro="Verificăm dacă Gemini poate citi site-ul tău. "
        "Aici lucrurile sunt tehnice, așa că le pregătim pentru persoana care îți face site-ul.",
        where_to_fix_ro="La persoana care îți face site-ul. Îi pregătim instrucțiunile exacte.",
    ),
    "info": ChapterTexts(
        name_ro="Aceleași informații peste tot",
        intro_ro="Gemini compară ce scrie despre tine pe Google, pe site și pe alte platforme. "
        "Dacă datele diferă, nu mai știe pe care să le creadă.",
        where_to_fix_ro="Pe fiecare platformă unde apari. Copiază datele de pe Profilul tău Google.",
    ),
    "mentiuni": ChapterTexts(
        name_ro="Mențiuni pe alte site-uri",
        intro_ro="Când alte site-uri vorbesc despre tine, Gemini află că ești cunoscut și de încredere.",
        where_to_fix_ro="În afara site-ului tău: bloguri, presă locală și liste cu recomandări. Îți pregătim mesajele.",
    ),
    "social": ChapterTexts(
        name_ro="Rețele sociale",
        intro_ro="Gemini se uită și pe Instagram și TikTok ca să afle cine ești și ce servești.",
        where_to_fix_ro="În aplicațiile Instagram și TikTok, din contul afacerii.",
    ),
    "cunoaste": ChapterTexts(
        name_ro="Te cunoaște deja Gemini?",
        intro_ro="L-am întrebat pe Gemini despre tine fără să-l lăsăm să caute pe internet, ca să vedem ce știe deja. "
        "Crește pe măsură ce rezolvi restul.",
        where_to_fix_ro=None,
    ),
}
"""The name, intro and „Unde se rezolvă” text of each chapter."""

GOOGLE_EDIT = ["Deschide Profilul tău Google din aplicația Google Maps."]
"""The first step of every Google profile fix."""

TEMPLATES: dict[str, CheckTemplate] = {
    "G01": CheckTemplate(
        label_ro="Profilul Google",
        title_ro="Creează-ți Profilul Google",
        solved_ro="Profilul tău Google există",
        why_ro="Fără profil, Gemini nu te poate arăta pe hartă și nu are de unde să afle programul, adresa sau recenziile.",
        steps_ro=[
            "Deschide Google Maps și caută adresa afacerii.",
            "Apasă Adaugă afacerea ta și urmează pașii.",
            "Confirmă afacerea cu codul primit de la Google.",
        ],
        evidence_ro="{status}",
    ),
    "G02": CheckTemplate(
        label_ro="Categoria de pe Google",
        title_ro="Categoria de pe Google nu se potrivește",
        solved_ro="Categoria „{category}” e setată",
        why_ro="Gemini folosește categoria ca să știe la ce întrebări să te recomande. "
        "Dacă e greșită, nu apari când cineva caută o {type_noun}.",
        steps_ro=[
            *GOOGLE_EDIT,
            "Apasă Editează profilul › Categoria afacerii.",
            "Alege „{type_label}” ca primă categorie și salvează.",
        ],
        evidence_ro="Categoria de acum: {category}.",
        where_ro="Profil › Editează profilul › Categoria afacerii",
        link="google",
    ),
    "G03": CheckTemplate(
        label_ro="Programul săptămânal",
        title_ro="Programul nu e complet pentru toată săptămâna",
        solved_ro="Programul e complet pentru toată săptămâna",
        why_ro="Gemini recomandă locurile despre care știe sigur când sunt deschise. Fără program complet, te poate lăsa deoparte.",
        steps_ro=[
            *GOOGLE_EDIT,
            "Apasă Editează profilul › Program.",
            "Completează orele pentru fiecare zi, inclusiv zilele în care e închis.",
        ],
        evidence_ro="Program completat pentru {days} din 7 zile.",
        where_ro="Profil › Editează profilul › Program",
        link="google",
    ),
    "G04": CheckTemplate(
        label_ro="Programul de sărbători",
        title_ro="Programul de sărbători lipsește",
        solved_ro="Programul de sărbători e setat",
        why_ro="Când cineva întreabă ce e deschis de sărbători, Gemini recomandă doar locurile cu program clar.",
        steps_ro=[
            *GOOGLE_EDIT,
            "Apasă Editează profilul › Program special.",
            "Adaugă programul pentru sărbătorile din următoarele două luni.",
        ],
        evidence_ro="Nu am găsit program special pentru următoarele 60 de zile.",
        where_ro="Profil › Editează profilul › Program special",
        link="google",
    ),
    "G05": CheckTemplate(
        label_ro="Fotografiile de pe Google",
        title_ro="Doar {photos}, recomandat minim 5",
        solved_ro="Ai cel puțin 5 fotografii",
        why_ro="Fotografiile cu interiorul, ce oferi și intrarea arată că locul e real și primitor, iar Gemini le ia în calcul.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Adaugă fotografii.", "Pune fotografii noi cu interiorul, ce oferi și intrarea."],
        evidence_ro="Am găsit {photos} pe Profilul tău Google.",
        where_ro="Profil › Fotografii › Adaugă fotografii",
        link="google",
    ),
    "G06": CheckTemplate(
        label_ro="Linkul către site",
        title_ro="Profilul Google nu are linkul către site",
        solved_ro="Linkul către site e pus",
        why_ro="Linkul îl ajută pe Gemini să lege profilul de site și să citească mai multe despre tine.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Editează profilul › Site web.", "Pune adresa site-ului și salvează."],
        where_ro="Profil › Editează profilul › Site web",
        link="google",
    ),
    "G07": CheckTemplate(
        label_ro="Numărul de telefon",
        title_ro="Lipsește numărul de telefon",
        solved_ro="Numărul de telefon e afișat",
        why_ro="Clienții vor să sune înainte să vină, iar Gemini preferă locurile cu date de contact complete.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Editează profilul › Telefon.", "Pune numărul și salvează."],
        where_ro="Profil › Editează profilul › Telefon",
        link="google",
    ),
    "G08": CheckTemplate(
        label_ro="Descrierea afacerii",
        title_ro="Fără descriere a afacerii",
        solved_ro="Profilul are o descriere",
        why_ro="Gemini folosește descrierea ca să înțeleagă ce te face special. "
        "Fără ea, alege {type_plural_definite} care spun mai mult despre ele.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Editează profilul › Descrierea afacerii.", "Lipește textul și salvează."],
        evidence_ro="Ai spus că profilul nu are încă o descriere.",
        where_ro="Profil › Editează profilul › Descrierea afacerii",
        max_chars=750,
        link="google",
    ),
    "G09": CheckTemplate(
        label_ro="Postările de pe Google",
        title_ro="Nicio postare în ultimele 30 de zile",
        solved_ro="Ai postat pe Google luna aceasta",
        why_ro="Postările recente arată că afacerea e activă. Una pe săptămână e de ajuns.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Adaugă actualizare.", "Lipește textul, adaugă o fotografie și publică."],
        evidence_ro="{when}",
        where_ro="Profil › Adaugă actualizare",
        link="google",
    ),
    "G10": CheckTemplate(
        label_ro="Detaliile despre afacere",
        title_ro="Lipsesc câteva detalii despre afacere",
        solved_ro="Detaliile importante sunt completate",
        why_ro="Detalii ca terasa sau plata cu cardul îl ajută pe Gemini să te recomande când cineva caută exact asta.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Editează profilul › Mai multe.", "Bifează tot ce se potrivește: {missing}."],
        evidence_ro="Lipsesc: {missing}.",
        where_ro="Profil › Editează profilul › Mai multe",
        link="google",
    ),
    "G11": CheckTemplate(
        label_ro="Nivelul de preț",
        title_ro="Lipsește nivelul de preț",
        solved_ro="Nivelul de preț e setat",
        why_ro="Mulți întreabă de locuri ieftine sau mai speciale. Cu prețurile setate, Gemini știe când să te recomande.",
        steps_ro=[*GOOGLE_EDIT, "Apasă Editează profilul › Mai multe › Prețuri.", "Alege intervalul de prețuri și salvează."],
        where_ro="Profil › Editează profilul › Mai multe › Prețuri",
        link="google",
    ),
    "G12": CheckTemplate(
        label_ro="Profilul revendicat",
        title_ro="Profilul nu e revendicat de tine",
        solved_ro="Profilul e revendicat de tine",
        why_ro="Doar după ce îl revendici poți schimba programul, descrierea și fotografiile și poți răspunde la recenzii.",
        steps_ro=[
            "Deschide Google Maps și caută afacerea.",
            "Apasă Revendică această afacere.",
            "Confirmă cu codul primit de la Google.",
        ],
        link="google",
    ),
    "R01": CheckTemplate(
        label_ro="Numărul de recenzii",
        title_ro="Mai puține recenzii decât {type_plural_definite} din jur",
        solved_ro="Ai cel puțin la fel de multe recenzii ca {type_plural_definite} din jur",
        why_ro="Gemini recomandă mai des locurile cu multe recenzii. Fiecare client mulțumit care scrie una te ajută.",
        steps_ro=[
            "Deschide Profilul tău Google și apasă Cere recenzii.",
            "Copiază linkul și trimite-l clienților mulțumiți.",
            "Pune un cod QR cu linkul la casă sau pe mese.",
        ],
        evidence_ro="Ai {reviews}, iar {type_plural_definite} din jur au în jur de {median}.",
        where_ro="Profil › Cere recenzii",
        link="google",
    ),
    "R02": CheckTemplate(
        label_ro="Nota medie",
        title_ro="Nota medie e {rating}, sub 4,6",
        solved_ro="Nota medie e foarte bună: {rating}",
        why_ro="Gemini recomandă mai ușor locurile cu note mari.",
        steps_ro=[
            "Citește recenziile cu 1–3 stele și vezi ce se repetă.",
            "Răspunde politicos la fiecare și spune ce ai schimbat.",
            "Cere recenzii clienților mulțumiți.",
        ],
        link="google",
    ),
    "R03": CheckTemplate(
        label_ro="Recenziile noi",
        title_ro="Nicio recenzie nouă în ultima lună",
        solved_ro="Ai recenzii noi luna aceasta",
        why_ro="Recenziile noi îi arată lui Gemini că locul e deschis și merită vizitat acum.",
        steps_ro=[
            "Cere o recenzie clienților fideli săptămâna asta.",
            "Folosește linkul din Profilul tău Google › Cere recenzii.",
        ],
        evidence_ro="Ultima recenzie e de acum {days}.",
        where_ro="Profil › Cere recenzii",
        link="google",
    ),
    "R04": CheckTemplate(
        label_ro="Răspunsurile la recenzii",
        title_ro="{unanswered} din ultimele {recent} fără răspuns",
        solved_ro="Răspunzi la recenzii",
        why_ro="Răspunsurile tale arată că îți pasă de clienți, iar Gemini le citește și pe ele.",
        steps_ro=[
            "Deschide Profilul tău Google › Recenzii.",
            "La fiecare recenzie fără răspuns, apasă Răspunde.",
            "Lipește răspunsul pregătit și trimite-l.",
        ],
        where_ro="Profil › Recenzii › Răspunde",
        link="google",
    ),
    "R05": CheckTemplate(
        label_ro="Recenzii pe o a doua platformă",
        title_ro="Nu ai recenzii pe {platform}",
        solved_ro="Ai recenzii și pe {platform}",
        why_ro="Gemini se uită și la recenziile de pe alte site-uri, nu doar pe Google.",
        steps_ro=["Creează profilul pe {platform}.", "Roagă câțiva clienți fideli să lase o recenzie și acolo."],
    ),
    "C01": CheckTemplate(
        label_ro="Numele și ce faci, pe prima pagină",
        title_ro="Prima pagină nu spune clar cine ești și ce faci",
        solved_ro="Numele și ce faci apar pe prima pagină",
        why_ro="Gemini citește prima pagină ca să afle ce fel de loc ești. Dacă nu scrie clar, ghicește sau te sare.",
        steps_ro=["Copiază textul pregătit.", "Pune-l la începutul primei pagini a site-ului."],
        link="website",
    ),
    "C02": CheckTemplate(
        label_ro="Adresa și cartierul, pe site",
        title_ro="Adresa și cartierul nu apar pe site",
        solved_ro="Adresa și cartierul apar pe site",
        why_ro="Când cineva caută o {type_noun} în {neighborhood}, Gemini caută cuvântul „{neighborhood}” și pe site-ul tău.",
        steps_ro=["Copiază textul pregătit cu adresa și cartierul.", "Pune-l pe prima pagină și pe pagina de contact."],
        link="website",
    ),
    "C03": CheckTemplate(
        label_ro="Programul, pe site",
        title_ro="Programul lipsește de pe site sau e altul decât pe Google",
        solved_ro="Programul de pe site e același ca pe Google",
        why_ro="Gemini răspunde des la întrebări ca „ce e deschis acum”. Fără programul corect pe site, nu are de unde să știe.",
        steps_ro=["Copiază programul pregătit.", "Pune-l pe prima pagină și pe pagina de contact."],
        evidence_ro="Pe Google: {expected}. Pe site: {found}.",
        link="website",
    ),
    "C04": CheckTemplate(
        label_ro="Telefonul, pe site",
        title_ro="Numărul de telefon nu apare pe site",
        solved_ro="Numărul de telefon apare pe site",
        why_ro="Un număr de telefon pe site îl ajută pe Gemini să confirme că e aceeași afacere ca pe Google.",
        steps_ro=["Copiază textul pregătit.", "Pune-l pe pagina de contact și în subsolul site-ului."],
        link="website",
    ),
    "C05": CheckTemplate(
        label_ro="{offer} și prețurile, pe site",
        title_ro="{offer} și prețurile nu sunt pe site",
        solved_ro="{offer} și prețurile sunt pe site, ca text",
        why_ro="Gemini nu poate citi o poză sau un PDF. Scris ca text, îl poate folosi când cineva întreabă ce oferi și cât costă.",
        steps_ro=[
            "Copiază textul pregătit.",
            "Pune-l pe o pagină a site-ului, ca text, nu ca poză.",
            "Adaugă prețul lângă fiecare produs sau serviciu.",
        ],
        evidence_ro="{found}",
        link="website",
    ),
    "C06": CheckTemplate(
        label_ro="Câte o pagină pentru fiecare categorie",
        title_ro="Nu ai câte o pagină pentru fiecare categorie",
        solved_ro="Fiecare categorie are pagina ei",
        why_ro="O pagină separată pentru fiecare categorie îl ajută pe Gemini să te recomande pentru fiecare.",
        steps_ro=DEV_STEPS,
    ),
    "C07": CheckTemplate(
        label_ro="Răspunsuri la întrebările clienților",
        title_ro="Site-ul nu răspunde la întrebările clienților",
        solved_ro="Site-ul răspunde la întrebările clienților",
        why_ro="Clienții întreabă de parcare, plata cu cardul sau rezervări. Dacă site-ul răspunde, Gemini preia răspunsul.",
        steps_ro=["Copiază întrebările și răspunsurile pregătite.", "Pune-le pe o pagină „Întrebări frecvente”."],
        evidence_ro="{found}",
        link="website",
    ),
    "C08": CheckTemplate(
        label_ro="Limba site-ului",
        title_ro="Site-ul nu e în română",
        solved_ro="Site-ul e în română",
        why_ro="Clienții tăi îl întreabă pe Gemini în română. Un site în română îl ajută să te potrivească cu întrebările lor.",
        steps_ro=["Copiază textele pregătite în română.", "Pune-le pe site, lângă sau în locul celor în altă limbă."],
        link="website",
    ),
    "T01": CheckTemplate(
        label_ro="Site-ul se deschide sigur",
        title_ro="Site-ul nu se deschide sigur",
        solved_ro="Site-ul se deschide sigur, cu HTTPS",
        why_ro="Dacă site-ul nu se deschide sau nu are HTTPS, Gemini nu îl citește deloc.",
        steps_ro=DEV_STEPS,
        evidence_ro="{found}",
    ),
    "T02": CheckTemplate(
        label_ro="Google și Gemini pot citi site-ul",
        title_ro="Unele pagini sunt închise pentru Gemini",
        solved_ro="Google și Gemini pot citi tot site-ul",
        why_ro="Unele pagini nu pot fi citite de Google sau de Gemini. Se rezolvă dintr-o setare a site-ului.",
        steps_ro=DEV_STEPS,
        evidence_ro="{found}",
    ),
    "T03": CheckTemplate(
        label_ro="Alți asistenți AI pot citi site-ul",
        title_ro="Alți asistenți AI nu pot citi site-ul",
        solved_ro="Și alți asistenți AI pot citi site-ul",
        why_ro="ChatGPT, Perplexity și Claude citesc site-ul doar dacă au voie. Se rezolvă dintr-o setare a site-ului.",
        steps_ro=DEV_STEPS,
        evidence_ro="Blocați: {found}.",
    ),
    "T04": CheckTemplate(
        label_ro="Informațiile se văd fără JavaScript",
        title_ro="Informațiile apar doar după ce pagina se încarcă complet",
        solved_ro="Informațiile se văd fără JavaScript",
        why_ro="Unii asistenți AI citesc doar textul trimis de server. Dacă adresa și programul apar abia după încărcare, ei nu le văd.",
        steps_ro=DEV_STEPS,
        evidence_ro="Lipsesc din codul trimis de server: {found}.",
    ),
    "T05": CheckTemplate(
        label_ro="Harta site-ului pentru Google",
        title_ro="Lipsește harta site-ului pentru Google",
        solved_ro="Site-ul are o hartă pentru Google",
        why_ro="Harta site-ului (sitemap) îi arată lui Google toate paginile, ca să nu rateze nimic.",
        steps_ro=DEV_STEPS,
    ),
    "T06": CheckTemplate(
        label_ro="Date pentru Gemini „pe limba lui”",
        title_ro="Site-ul nu îi spune lui Gemini programul și adresa „pe limba lui”",
        solved_ro="Site-ul îi dă lui Gemini datele „pe limba lui”",
        why_ro="Câteva rânduri invizibile pentru clienți îi dau lui Gemini datele exacte. "
        "Le pregătim noi pentru cel care îți face site-ul.",
        steps_ro=DEV_STEPS,
        evidence_ro="{found}",
    ),
    "T07": CheckTemplate(
        label_ro="Viteza pe telefon",
        title_ro="Site-ul se încarcă greu pe telefon",
        solved_ro="Site-ul se încarcă repede pe telefon",
        why_ro="Dacă pagina se deschide greu, Gemini o citește mai rar și mai puțin.",
        steps_ro=DEV_STEPS,
        evidence_ro="{found}",
    ),
    "T08": CheckTemplate(
        label_ro="Site-ul se vede bine pe telefon",
        title_ro="Site-ul nu e făcut pentru telefon",
        solved_ro="Site-ul se vede bine pe telefon",
        why_ro="Cei mai mulți clienți caută de pe telefon. Un site care nu se adaptează e citit și arătat mai rar.",
        steps_ro=DEV_STEPS,
    ),
    "T09": CheckTemplate(
        label_ro="O pagină cu informațiile de bază",
        title_ro="Gemini nu găsește o pagină cu informațiile de bază",
        solved_ro="Ai o pagină cu toate informațiile de bază",
        why_ro="Adresa, programul și ce oferi sunt împrăștiate sau lipsesc. O singură pagină clară îl ajută pe Gemini să te înțeleagă.",
        steps_ro=[
            "Verifică pagina pregătită și completează ce e marcat cu galben.",
            "Trimite-o persoanei care îți face site-ul.",
        ],
    ),
    "L01": CheckTemplate(
        label_ro="Platformele potrivite",
        title_ro="Nu apari pe {missing}",
        solved_ro="Apari pe toate platformele potrivite",
        why_ro="Clienții și Gemini caută și pe aceste platforme. Cu cât apari în mai multe locuri potrivite, cu atât ești mai ușor de găsit.",
        steps_ro=["Creează profilul pe {missing}.", "Folosește aceleași date ca pe Profilul tău Google."],
        evidence_ro="Apari pe {present} din {expected} platforme potrivite.",
    ),
    "L02": CheckTemplate(
        label_ro="Aceleași date pe toate platformele",
        title_ro="Datele diferă de la o platformă la alta",
        solved_ro="Datele sunt aceleași peste tot",
        why_ro=DIFFERENT_DATA_WHY,
        steps_ro=["Copiază datele de pe Profilul tău Google pe fiecare platformă."],
    ),
    "L02:name": CheckTemplate(
        label_ro="Numele de pe {source}",
        title_ro="Numele de pe {source} e diferit de cel de pe Google",
        solved_ro="Numele de pe {source} e același ca pe Google",
        why_ro=DIFFERENT_DATA_WHY,
        steps_ro=["Intră în contul tău de pe {source}.", "Pune numele de pe Profilul tău Google.", "Salvează."],
        evidence_ro="{source}: {found}. Google: {expected}.",
    ),
    "L02:address": CheckTemplate(
        label_ro="Adresa de pe {source}",
        title_ro="Adresa de pe {source} e diferită de cea de pe Google",
        solved_ro="Adresa de pe {source} e aceeași ca pe Google",
        why_ro=DIFFERENT_DATA_WHY,
        steps_ro=["Intră în contul tău de pe {source}.", "Pune adresa de pe Profilul tău Google.", "Salvează."],
        evidence_ro="{source}: {found}. Google: {expected}.",
    ),
    "L02:phone": CheckTemplate(
        label_ro="Telefonul de pe {source}",
        title_ro="Telefonul de pe {source} e diferit de cel de pe Google",
        solved_ro="Telefonul de pe {source} e același ca pe Google",
        why_ro=DIFFERENT_DATA_WHY,
        steps_ro=["Intră în contul tău de pe {source}.", "Pune numărul de telefon de pe Profilul tău Google.", "Salvează."],
        evidence_ro="{source}: {found}. Google: {expected}.",
    ),
    "L02:hours": CheckTemplate(
        label_ro="Programul de pe {source}",
        title_ro="Programul de pe {source} e diferit de cel de pe Google",
        solved_ro="Programul de pe {source} e același ca pe Google",
        why_ro=DIFFERENT_DATA_WHY,
        steps_ro=["Intră în contul tău de pe {source}.", "Pune programul de pe Profilul tău Google.", "Salvează."],
        evidence_ro="{source}: {found}. Google: {expected}.",
    ),
    "M01": CheckTemplate(
        label_ro="Site-uri care vorbesc despre tine",
        title_ro="Prea puține site-uri vorbesc despre tine",
        solved_ro="Multe site-uri vorbesc despre tine",
        why_ro="Gemini are mai multă încredere în locurile despre care scriu și alții: bloguri, presă, ghiduri ale orașului.",
        steps_ro=[
            "Invită bloggerii din {city} care scriu despre {type_plural} să te viziteze.",
            "Roagă-ți partenerii și furnizorii să te menționeze pe site-ul lor.",
        ],
        evidence_ro="Am găsit mențiuni pe {sites}.",
    ),
    "M02": CheckTemplate(
        label_ro="Topuri și recomandări",
        title_ro="Nu apari în niciun top",
        solved_ro="Apari în cel puțin un top",
        why_ro="Când cineva cere „cele mai bune {type_plural}”, Gemini citește topurile făcute de alții.",
        steps_ro=["Caută topurile de {type_plural} din {city}.", "Scrie-le autorilor un mesaj scurt despre tine."],
    ),
    "M03": CheckTemplate(
        label_ro="Presa locală",
        title_ro="Presa locală nu a scris despre tine",
        solved_ro="Presa locală a scris despre tine",
        why_ro="Un articol într-o publicație locală îi arată lui Gemini că ești un loc cunoscut în cartier.",
        steps_ro=["Copiază e-mailul pregătit.", "Trimite-l unei publicații sau unui blog local."],
    ),
    "M05": CheckTemplate(
        label_ro="Forumuri și grupuri",
        title_ro="Nimeni nu vorbește despre tine pe forumuri",
        solved_ro="Oamenii vorbesc despre tine pe forumuri",
        why_ro="Gemini citește și discuțiile de pe forumuri și grupuri, unde oamenii își recomandă locurile preferate.",
        steps_ro=[
            "Răspunde când cineva cere recomandări de {type_plural} în {neighborhood}.",
            "Spune clar că ești proprietarul.",
        ],
    ),
    "S02": CheckTemplate(
        label_ro="Profilul de Instagram",
        title_ro="Nu am găsit profilul de Instagram",
        solved_ro="Profilul de Instagram există",
        why_ro="Mulți clienți caută pe Instagram, iar Gemini se uită și acolo ca să afle cum arată locul.",
        steps_ro=[
            "Creează un profil de Instagram pentru afacere sau verifică dacă linkul e corect.",
            "Treci profilul pe cont de afacere sau de creator.",
        ],
        evidence_ro="{found}",
        link="instagram",
    ),
    "S03": CheckTemplate(
        label_ro="Postările recente",
        title_ro="Nicio postare nouă în ultimele 30 de zile",
        solved_ro="Ai postat luna aceasta",
        why_ro="Postările recente arată că afacerea e activă și merită recomandată.",
        steps_ro=["Copiază ideea de postare pregătită.", "Publică o fotografie sau un clip scurt."],
        evidence_ro="{found}",
        link="instagram",
    ),
    "S04": CheckTemplate(
        label_ro="Linkurile dintre site, Instagram și Google",
        title_ro="Lipsesc linkurile dintre site, Instagram și Profilul Google",
        solved_ro="Site-ul, Instagram și Profilul Google au linkuri unele către altele",
        why_ro="Linkurile îl ajută pe Gemini să lege site-ul de Instagram și de Profilul tău Google.",
        steps_ro=[
            "Pune pe site linkul către Instagram.",
            "Pune linkul site-ului în descrierea de pe Instagram.",
            "Verifică să fie și pe Profilul tău Google.",
        ],
        evidence_ro="Lipsesc: {missing}.",
    ),
    "S05": CheckTemplate(
        label_ro="Descrierea de pe Instagram",
        title_ro="Descrierea de pe Instagram nu spune ce faci și unde ești",
        solved_ro="Descrierea de pe Instagram spune ce faci și unde ești",
        why_ro="Gemini citește descrierea profilului ca să afle ce oferi și în ce cartier ești.",
        steps_ro=["În Instagram: Profil › Editează profilul › Biografie, apoi lipește textul și salvează."],
        evidence_ro="Descrierea de acum: „{found}”.",
        where_ro="Profil › Editează profilul › Biografie",
        max_chars=150,
        link="instagram",
    ),
    "K01": CheckTemplate(
        label_ro="Gemini știe că exiști",
        title_ro="Gemini nu știe încă de tine",
        solved_ro="Gemini știe că exiști",
        why_ro="Fără să caute pe internet, Gemini nu te cunoaște. Crește pe măsură ce rezolvi restul.",
        steps_ro=[],
    ),
    "K02": CheckTemplate(
        label_ro="Gemini știe ce faci și unde ești",
        title_ro="Gemini nu știe ce faci și unde ești",
        solved_ro="Gemini știe ce faci și unde ești",
        why_ro="Crește pe măsură ce rezolvi restul.",
        steps_ro=[],
    ),
    "K03": CheckTemplate(
        label_ro="Gemini nu spune lucruri greșite",
        title_ro="Gemini spune lucruri greșite despre tine",
        solved_ro="Gemini nu spune lucruri greșite despre tine",
        why_ro="Crește pe măsură ce rezolvi restul.",
        steps_ro=[],
    ),
}
"""The texts of every check; per-field listing checks use `L02:<field>`."""

DEEP_LINK_LABELS: dict[LinkKind, str] = {
    "google": "Deschide Profilul tău Google",
    "website": "Deschide site-ul",
    "instagram": "Deschide Instagram",
    "tiktok": "Deschide TikTok",
}
"""The button label of each deep link."""


class TextParams(dict[str, str]):
    """Template values; a placeholder without a value renders empty instead of failing the report."""

    def __missing__(self, _: str) -> str:
        """Returns an empty value for a placeholder the check didn't fill."""
        return ""


def get_context(business: Business) -> dict[str, str]:
    """Returns the business values every template can use."""
    nouns = TYPE_NOUNS[business.type]
    return {
        "name": business.name,
        "city": business.city,
        "neighborhood": business.neighborhood,
        "type_label": business.type_label_ro,
        "type_noun": nouns.singular,
        "type_plural": nouns.plural,
        "type_plural_definite": nouns.plural_definite,
        "offer": nouns.offer,
    }


def get_template(check_id: str) -> CheckTemplate:
    """Returns the texts of a check; „L02:<source>:<field>” uses the template of its field."""
    parts = check_id.split(":")
    if len(parts) == 3:
        return TEMPLATES[f"{parts[0]}:{parts[2]}"]
    return TEMPLATES[check_id]


def get_panel(check_id: str) -> FixPanel:
    """Returns the side panel a problem opens."""
    if check_id == "T09":
        return "info_page"
    fix_type = get_catalog_entry(check_id).fix_type
    if fix_type == "generate":
        return "generate_text"
    if fix_type == "dev_export":
        return "dev_export"
    return "steps"


def get_deep_link(link: LinkKind | None, panel: FixPanel, business: Business) -> tuple[str | None, str | None]:
    """Returns a problem's deep link and its button label; the Instagram text panel copies before opening."""
    url = (
        {
            "google": business.google_maps_uri,
            "website": business.website,
            "instagram": business.instagram_url,
            "tiktok": business.tiktok_url,
        }.get(link)
        if link
        else None
    )
    if url is None or link is None:
        return None, None
    if link == "instagram" and panel == "generate_text":
        return url, "Copiază și deschide Instagram"
    return url, DEEP_LINK_LABELS[link]


def get_params(check: CheckResult, context: dict[str, str]) -> TextParams:
    """Returns the values a check's texts are filled with: the business context, the check's params and its evidence."""
    return TextParams(
        {
            **context,
            "found": check.evidence.found or "",
            "expected": check.evidence.expected or "",
            **check.params,
        }
    )


def build_problem(check: CheckResult, chapter_checks: list[CheckResult], business: Business) -> Problem:
    """Returns the problem card for a failed or partial check."""
    template = get_template(check.check_id)
    params = get_params(check, get_context(business))
    panel = get_panel(check.check_id)
    deep_link, deep_link_label = get_deep_link(template.link, panel, business)
    points = get_problem_points(check, chapter_checks)
    evidence = template.evidence_ro.format_map(params).strip() if template.evidence_ro else ""
    return Problem(
        check_id=check.check_id,
        chapter_id=check.chapter_id,
        chapter_name_ro=CHAPTER_TEXTS[check.chapter_id].name_ro,
        title_ro=template.title_ro.format_map(params),
        why_ro=template.why_ro.format_map(params),
        points=points,
        impact=round(points * CHAPTER_WEIGHTS[check.chapter_id], 4),
        fix_type=get_catalog_entry(check.check_id).fix_type,
        fix=FixPayload(
            panel=panel,
            steps_ro=[step.format_map(params) for step in template.steps_ro],
            deep_link=deep_link,
            deep_link_label_ro=deep_link_label,
            where_ro=template.where_ro,
            max_chars=template.max_chars,
            evidence_ro=evidence or None,
        ),
    )


def build_chapter(chapter_id: ChapterId, all_checks: list[CheckResult], business: Business) -> Chapter:
    """Returns a chapter built from its checks: score, open problems, solved items and checks that couldn't run."""
    checks = [check for check in all_checks if check.chapter_id == chapter_id]
    context = get_context(business)
    texts = CHAPTER_TEXTS[chapter_id]
    has_fixes = chapter_id != "cunoaste"
    problems = [
        build_problem(check, checks, business)
        for check in checks
        if has_fixes and check.status in ("fail", "partial") and not check.claimed_fixed
    ]
    solved = [
        SolvedItem(
            check_id=check.check_id,
            title_ro=get_template(check.check_id).solved_ro.format_map(get_params(check, context)),
            source="passed",
            points=None,
        )
        for check in checks
        if check.status == "pass"
    ] + [
        SolvedItem(
            check_id=check.check_id,
            title_ro=get_template(check.check_id).title_ro.format_map(get_params(check, context)),
            source="claimed_fixed",
            points=get_problem_points(check, checks),
        )
        for check in checks
        if check.claimed_fixed
    ]
    unknown = [
        UnknownItem(
            check_id=check.check_id,
            title_ro=get_template(check.check_id).label_ro.format_map(get_params(check, context)),
            reason_ro=check.reason_ro or "Nu am putut verifica acum.",
        )
        for check in checks
        if check.status == "unknown"
    ]
    return Chapter(
        id=chapter_id,
        name_ro=texts.name_ro,
        intro_ro=texts.intro_ro.format_map(TextParams(context)),
        where_to_fix_ro=texts.where_to_fix_ro,
        score=get_chapter_score(chapter_id, checks, all_checks),
        weight=CHAPTER_WEIGHTS[chapter_id],
        possible_points=0,
        overall_gain_if_all_fixed=0,
        has_fixes=has_fixes,
        problems=problems,
        solved=solved,
        unknown=unknown,
    )


def build_chapters(checks: list[CheckResult], business: Business) -> list[Chapter]:
    """Returns the eight chapters in order; totals are filled in by `refresh_report_totals`."""
    return [build_chapter(chapter_id, checks, business) for chapter_id in CHAPTER_WEIGHTS]
