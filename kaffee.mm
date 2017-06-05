<map version="freeplane 1.5.9">
<!--To view this file, download free mind mapping software Freeplane from http://freeplane.sourceforge.net -->
<node TEXT="Kaffee_RFID" FOLDED="false" ID="ID_1563772046" CREATED="1483961227130" MODIFIED="1486454070241"><hook NAME="MapStyle" zoom="1.235">
    <properties fit_to_viewport="false;" show_note_icons="true" show_icon_for_attributes="true" show_notes_in_map="false"/>

<map_styles>
<stylenode LOCALIZED_TEXT="styles.root_node" STYLE="oval" UNIFORM_SHAPE="true" VGAP_QUANTITY="24.0 pt">
<font SIZE="24"/>
<stylenode LOCALIZED_TEXT="styles.predefined" POSITION="right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="default" COLOR="#000000" STYLE="fork">
<font NAME="SansSerif" SIZE="10" BOLD="false" ITALIC="false"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.details"/>
<stylenode LOCALIZED_TEXT="defaultstyle.attributes">
<font SIZE="9"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.note" COLOR="#000000" BACKGROUND_COLOR="#ffffff" TEXT_ALIGN="LEFT"/>
<stylenode LOCALIZED_TEXT="defaultstyle.floating">
<edge STYLE="hide_edge"/>
<cloud COLOR="#f0f0f0" SHAPE="ROUND_RECT"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.user-defined" POSITION="right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="styles.topic" COLOR="#18898b" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subtopic" COLOR="#cc3300" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subsubtopic" COLOR="#669900">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.important">
<icon BUILTIN="yes"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.AutomaticLayout" POSITION="right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="AutomaticLayout.level.root" COLOR="#000000" STYLE="oval" SHAPE_HORIZONTAL_MARGIN="10.0 pt" SHAPE_VERTICAL_MARGIN="10.0 pt">
<font SIZE="18"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,1" COLOR="#0033ff">
<font SIZE="16"/>
<edge COLOR="#ff0000"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,2" COLOR="#00b439">
<font SIZE="14"/>
<edge COLOR="#0000ff"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,3" COLOR="#990000">
<font SIZE="12"/>
<edge COLOR="#00ff00"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,4" COLOR="#111111">
<font SIZE="10"/>
<edge COLOR="#ff00ff"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,5">
<edge COLOR="#00ffff"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,6">
<edge COLOR="#7c0000"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,7">
<edge COLOR="#00007c"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,8">
<edge COLOR="#007c00"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,9">
<edge COLOR="#7c007c"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,10">
<edge COLOR="#007c7c"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,11">
<edge COLOR="#7c7c00"/>
</stylenode>
</stylenode>
</stylenode>
</map_styles>
</hook>
<hook NAME="accessories/plugins/AutomaticLayout.properties" VALUE="ALL"/>
<hook NAME="AutomaticEdgeColor" COUNTER="8" RULE="FOR_BRANCHES"/>
<node TEXT="Version 1.0 (Funktion)" LOCALIZED_STYLE_REF="AutomaticLayout.level.root" POSITION="left" ID="ID_1908744180" CREATED="1486453714681" MODIFIED="1486472701723">
<node TEXT="Displaysteuerung" ID="ID_1419007001" CREATED="1484047728514" MODIFIED="1486454400825" STYLE="bubble">
<edge COLOR="#33ff00"/>
<node TEXT="AUS" ID="ID_55936029" CREATED="1484047735327" MODIFIED="1486454070256">
<node TEXT="Bei Leerlauf" ID="ID_1095412704" CREATED="1484047746921" MODIFIED="1486454070256"/>
</node>
<node TEXT="EIN" ID="ID_1192603284" CREATED="1484047758890" MODIFIED="1486454070256">
<node TEXT="Bei RFID Anmeldung" ID="ID_225969218" CREATED="1484047761843" MODIFIED="1486454070256">
<node TEXT="1. Anzeige Preis Kaffe&#xa;&#xa;1a. Anzeige Name&#xa;2a. Anzeige Kontostand&#xa;&#xa;Ab Wasserfluss:&#xa;Anzeige neuer Kontostand" ID="ID_1346274144" CREATED="1484047772405" MODIFIED="1486473670740">
<cloud COLOR="#f0f0f0" SHAPE="ARC"/>
</node>
</node>
<node TEXT="Registrierung" ID="ID_492569800" CREATED="1484047886628" MODIFIED="1486461483581">
<node TEXT="1.Anzeige RFID Tag&#xa;2.Anzeige zugeordneter Name" ID="ID_1751704379" CREATED="1484047904472" MODIFIED="1486461483581">
<cloud COLOR="#f0f0f0" SHAPE="ARC"/>
</node>
</node>
</node>
</node>
<node TEXT="Datenbank SQLite" ID="ID_903068201" CREATED="1483961476735" MODIFIED="1486454394137" COLOR="#0000ff" STYLE="bubble">
<edge COLOR="#0000ff"/>
<node TEXT="Struktur" ID="ID_1716578136" CREATED="1483961485032" MODIFIED="1486454070256">
<node TEXT="Benutzerdb" ID="ID_1710746678" CREATED="1484047236031" MODIFIED="1486454070256">
<node TEXT="RFID Tag" ID="ID_454118484" CREATED="1483961546424" MODIFIED="1486454070256"/>
<node TEXT="Vorname" ID="ID_1254915650" CREATED="1483961834070" MODIFIED="1486454070256"/>
<node TEXT="Name" ID="ID_571864221" CREATED="1483961551596" MODIFIED="1486454070256"/>
<node TEXT="Kontostand" ID="ID_1262193830" CREATED="1483961555361" MODIFIED="1486454070256"/>
</node>
<node TEXT="Configdb" ID="ID_1555175192" CREATED="1484047258218" MODIFIED="1486454070256">
<node TEXT="Kaffeepreis" ID="ID_1463907608" CREATED="1484047273812" MODIFIED="1486454070256"/>
<node TEXT="maximaler Kredit" ID="ID_516495914" CREATED="1484047290813" MODIFIED="1486454070256"/>
</node>
<node TEXT="Kasse" ID="ID_624786183" CREATED="1486453602804" MODIFIED="1486454070256">
<node TEXT="Datum" ID="ID_157989814" CREATED="1486453617398" MODIFIED="1486454070256"/>
<node TEXT="Vorname" ID="ID_1553898494" CREATED="1486453621445" MODIFIED="1486454070256"/>
<node TEXT="Name" ID="ID_338957572" CREATED="1486453626101" MODIFIED="1486454070256"/>
<node TEXT="Betrag" ID="ID_1506581840" CREATED="1486453631992" MODIFIED="1486454070256"/>
</node>
<node TEXT="Statistik" ID="ID_599159262" CREATED="1486454137242" MODIFIED="1486454143258">
<node TEXT="Monatsverbrauch Kaffee" ID="ID_502349809" CREATED="1486454150805" MODIFIED="1486454163242"/>
<node TEXT="Kassenstand" ID="ID_1674881157" CREATED="1486454172414" MODIFIED="1486454184430"/>
<node TEXT="Differenz Kasse" ID="ID_1310824141" CREATED="1486454193071" MODIFIED="1486454199087"/>
</node>
</node>
</node>
<node TEXT="Funktionen" ID="ID_76609238" CREATED="1486453993395" MODIFIED="1486454389231" COLOR="#cc0000" STYLE="bubble">
<node TEXT="Hauptmodul" FOLDED="true" ID="ID_111057454" CREATED="1483961371012" MODIFIED="1486454070256">
<node TEXT="Endlosschleife" ID="ID_1694176115" CREATED="1483961383374" MODIFIED="1486473709147"><richcontent TYPE="NOTE">

<html>
  <head>
    
  </head>
  <body>
    <p>
      &#220;berwachung des RFID lesers, bei Erfassung Verbuchung des eingestellten Preises auf die Karte, anschlie&#223;end Freigabe der Tasten f&#252;r 1x Kaffee, verbuchung ab Wasserfluss, damit bei leeren Bohnen ein Abbruch ohne Kosten m&#246;glich ist
    </p>
  </body>
</html>

</richcontent>
</node>
</node>
<node TEXT="Men&#xfc;" ID="ID_813697659" CREATED="1486454252213" MODIFIED="1486454255853">
<node TEXT="Benutzerverwaltung" ID="ID_273978487" CREATED="1483961301817" MODIFIED="1486459794622">
<node TEXT="Registrierung" ID="ID_1311916301" CREATED="1484047345548" MODIFIED="1486454070256"/>
<node TEXT="L&#xf6;schung" ID="ID_982952610" CREATED="1484047351829" MODIFIED="1486454070256"/>
</node>
<node TEXT="Bezahlen" ID="ID_870454657" CREATED="1483961310301" MODIFIED="1486454070256"/>
<node TEXT="Statistik" ID="ID_1074496839" CREATED="1483961339864" MODIFIED="1486454070256"/>
</node>
</node>
</node>
</node>
</map>
