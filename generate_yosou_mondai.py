# -*- coding: utf-8 -*-
"""
ビルクリーニング技能検定 基礎級 - 予想問題 自動生成ツール（ローカル・オフライン版）

つかいかた:
    python generate_yosou_mondai.py
    python generate_yosou_mondai.py --count 25
    python generate_yosou_mondai.py --count 30 --seed 42 --no-open

Anthropic の API や インターネット接続は つかいません。
じっこうする たびに、どうぐ・せんざい・マナー などの ちしきベースから
ランダムに ○×もんだいを くみあわせて つくります。
"""
import argparse
import datetime
import json
import os
import random
import webbrowser

# ============================================================
# かな -> ローマじ へんかん（かんいHepburn。ー は "-" で ひょうげん）
# ============================================================
COMBO_MAP = {
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ふぃ": "fi", "うぃ": "wi", "てぃ": "ti", "でぃ": "di",
}
SINGLE_MAP = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
}


def _kana_to_romaji(kana_word):
    i, n = 0, len(kana_word)
    result = ""
    pending_sokuon = False
    while i < n:
        ch = kana_word[i]
        if ch == "ー":
            result += "-"
            i += 1
            continue
        if ch == "っ":
            pending_sokuon = True
            i += 1
            continue
        two = kana_word[i:i + 2]
        if two in COMBO_MAP:
            syll = COMBO_MAP[two]
            i += 2
        elif ch in SINGLE_MAP:
            syll = SINGLE_MAP[ch]
            i += 1
        elif ch == "ん":
            nxt_syll = ""
            if i + 1 < n:
                two2 = kana_word[i + 1:i + 3]
                if two2 in COMBO_MAP:
                    nxt_syll = COMBO_MAP[two2]
                elif kana_word[i + 1] in SINGLE_MAP:
                    nxt_syll = SINGLE_MAP[kana_word[i + 1]]
            if nxt_syll and nxt_syll[0] in "aiueoy":
                result += "n'"
            else:
                result += "n"
            i += 1
            continue
        else:
            result += ch
            i += 1
            continue
        if pending_sokuon:
            syll = ("t" + syll) if syll.startswith("ch") else (syll[0] + syll)
            pending_sokuon = False
        result += syll
    return result


def sentence_to_romaji(hira_sentence):
    """スペースくぎりの ひらがな文を ローマじに へんかんする。
    は/へ/を は じょし として わ/え/うぉ に とくべつしょりする。"""
    normalized = hira_sentence.replace("、", "、 ").replace("。", "。 ")
    tokens = [t for t in normalized.split(" ") if t != ""]
    out = []
    for idx, tok in enumerate(tokens):
        trailing = ""
        core = tok
        while core and core[-1] in "。、":
            trailing = core[-1] + trailing
            core = core[:-1]
        trailing = trailing.replace("。", ".").replace("、", ",")
        if core == "は":
            romaji = "wa"
        elif core == "へ":
            romaji = "e"
        elif core == "を":
            romaji = "wo"
        else:
            romaji = _kana_to_romaji(core)
        if idx == 0 and romaji:
            romaji = romaji[0].upper() + romaji[1:]
        out.append(romaji + trailing)
    return " ".join(out)


# ============================================================
# ちしきベース 1: どうぐ と そのもくてき（くみあわせで もんだいを つくる）
# ============================================================
TOOLS = [
    ("じざいぼうき", "ゆか の ごみ を はく"),
    ("かんしき もっぷ", "ゆか の ほこり を とる"),
    ("しっしき もっぷ", "ゆか を みずぶき する"),
    ("ふろあー すくいじー", "ゆか の みず を あつめる"),
    ("ういんど すくいじー", "まどがらす の みず を きる"),
    ("ぱてないふ", "こびりついた よごれ を こそげとる"),
    ("けかき", "ほうき の け に からまった かみのけ や ほこり を て を つかわずに とりのぞく"),
    ("だすと こんとろーる", "みず を つかわずに ほこり を とる"),
    ("ふろあー ぽりっしゃー", "ゆか を みがく"),
    ("そうじき", "ごみ や ほこり を すいとる"),
    ("ぶんかちりとり", "はきあつめた ごみ を いれる"),
    ("でっきぶらし", "ゆか の がんこな よごれ を こする"),
    ("だいしゃ", "たいりょう の ごみ を はこぶ"),
    ("きゃたつ", "たかい ばしょ の さぎょう を する"),
    ("ごむてぶくろ", "て を まもりながら せんざい を つかう"),
    ("あんぜんくつ", "すべりにくく して てんとう を ふせぐ"),
]

# ============================================================
# ちしきベース 2: よごれ と つかう せんざいの せいしつ
# ============================================================
DETERGENT_TYPES = ["さんせい", "あるかりせい", "ちゅうせい"]
DIRTS = [
    ("べんき の にょうせき", "さんせい"),
    ("ゆか の あぶら よごれ", "あるかりせい"),
    ("まいにち の かるい よごれ", "ちゅうせい"),
    ("りのりうむ ゆか の にちじょう そうじ", "ちゅうせい"),
    ("すてんれす の みずあか", "さんせい"),
    ("ちゅうぼう の あぶら よごれ", "あるかりせい"),
    ("かがみ の みずあか", "さんせい"),
    ("ゆか の わっくす かす", "あるかりせい"),
]

# ============================================================
# ちしきベース 3: マナー・あんぜん・えいせい など（正/誤 の ペア）
# ============================================================
STATIC_FACTS = [
    ("さぎょう を はじめる まえ に、みだしなみ を かくにんする。",
     "さぎょう を はじめる まえ でも、みだしなみ は きにしなくて よい。",
     "せいけつな みだしなみ は、りようしゃ に あんしんかん を あたえる たいせつな まなーです。"),
    ("せんざい を つかう とき は、せいひん の ひょうじ を よく よんでから つかう。",
     "せんざい は ひょうじ を よまずに つかっても もんだいない。",
     "せんざい には つかいかた や ちゅういてん が きさいされている ため、かならず ひょうじ を かくにんします。"),
    ("ごむてぶくろ は て を ほごする ため に つかう。",
     "ごむてぶくろ は さぎょう を はやく する ため に つかう。",
     "ごむてぶくろ の もくてき は、せんざい や よごれ から て を まもる こと です。"),
    ("こうたいじかん が きたら、つぎ の ひと に さぎょう の じょうきょう を つたえる。",
     "こうたいじかん が きても、つぎ の ひと に なにも つたえなくて よい。",
     "さぎょう の ひきつぎ を きちんと おこなう こと で、せいそう の ぬけ を ふせぎます。"),
    ("ふるい せんざい や やくざい は、きめられた ほうほう で はいきする。",
     "ふるい せんざい や やくざい は、どんな ほうほう で すてても よい。",
     "やくざい の しゅるい に よって はいきほうほう が きめられている ため、かってに すてては いけません。"),
    ("えれべーたー の せいそうちゅう は、あんぜんに りようできるよう ひょうじ を だす。",
     "えれべーたー の せいそうちゅう は、なにも ひょうじしなくて よい。",
     "りようしゃ が あんぜんに とおれるよう、さぎょうちゅう の ひょうじ が ひつようです。"),
    ("みず を つかう さぎょう で は、すべりにくい くつ を えらぶ こと が たいせつ で ある。",
     "みず を つかう さぎょう で も、どんな くつ でも かまわない。",
     "みず で ぬれた ゆか は すべりやすい ため、あんぜんな くつ を えらびます。"),
    ("せいそうようざい の ほかんばしょ は、こども が さわれない ところ に する。",
     "せいそうようざい は どこ に おいても かまわない。",
     "やくひん は あんぜん の ため、て の とどかない ばしょ に ほかんします。"),
    ("きゅうな こしょう を みつけたら、かかり の ひと に ほうこくする。",
     "きゅうな こしょう を みつけても、じぶん で しゅうりすれば よい。",
     "せんもんがい の しゅうり は じこ の げんいん に なる ため、かかり の ひと に ほうこくします。"),
    ("ゆか を みがく まえ に、こまかい ごみ を とりのぞく。",
     "ゆか を みがく まえ でも、ごみ が あって もんだいない。",
     "ごみ が のこった まま みがくと、ゆか に きず が つく こと が あります。"),
    ("においの きつい やくざい を つかう とき は、かんき に き を つける。",
     "においの きつい やくざい で も、かんき は きにしなくて よい。",
     "かんき を おこなわないと、たいちょう を くずす げんいん に なります。"),
    ("せいそう の さぎょうちゅう は、りようしゃ の つうこう を さまたげないように する。",
     "せいそう の さぎょうちゅう は、りようしゃ の つうこう は きにしなくて よい。",
     "りようしゃ の あんぜん と べんりせい を かんがえて さぎょうする こと が たいせつです。"),
    ("かび は しっけ の おおい ばしょ に はっせいしやすい。",
     "かび は かんそうした ばしょ に はっせいしやすい。",
     "かび は しっけ と よごれ の おおい ばしょ で そだちやすい ため、かんき と せいそう が たいせつです。"),
    ("せいそう の けいかくひょう を つくる こと で、さぎょう の ぬけ を ふせげる。",
     "せいそう の けいかくひょう は つくらなくても よい。",
     "けいかくひょう が ある こと で、どこ を いつ そうじする か が めいかく に なります。"),
    ("びひん は なくなる まえ に ほじゅうする。",
     "びひん は なくなってから ほじゅうすれば よい。",
     "りようしゃ が こまらないよう、びひん は なくなる まえ に ほじゅうします。"),
    ("がらすそうじ の あと は、ふきむら が ないか かくにんする。",
     "がらすそうじ の あと は、かくにんしなくても よい。",
     "ふきむら が のこっていないか さいご に かくにんする こと で、しあがり が よくなります。"),
    ("せいそうどうぐ は しゅるいごとに せいりして ほかんする。",
     "せいそうどうぐ は どこ に おいても よい。",
     "どうぐ を せいりして ほかんする こと で、つぎ に つかう とき すぐ みつけられます。"),
    ("かいだん の てすり も せいそう の たいしょう に なる。",
     "かいだん の てすり は そうじしなくて よい。",
     "てすり は おおくの ひと が さわる ばしょ なので、えいせい の ため せいそうします。"),
    ("えあこん の ふぃるたー に は ほこり が たまりやすい。",
     "えあこん の ふぃるたー に は ほこり が たまらない。",
     "ふぃるたー に ほこり が たまると、くうき の ながれ が わるくなり こうりつ が さがります。"),
    ("ゆか に わっくす を ぬる とき は、うすく きんいつ に ぬる。",
     "ゆか に わっくす を ぬる とき は、あつく いちぶ だけ に ぬる。",
     "あつぬり や むらぬり は、しあがり が わるくなる げんいん に なります。"),
    ("せいそう の しごと で は、じかん を まもって こうどうする。",
     "せいそう の しごと で は、じかん は きにしなくて よい。",
     "じかんげんしゅ は、しごと に たいする しんらい に つながる たいせつな しゅうかんです。"),
    ("がらす の われめ を みつけたら、かかり の ひと に ほうこくする。",
     "がらす の われめ を みつけても、そのまま に しておく。",
     "われた がらす は きけんな ので、みつけたら すぐ に ほうこくします。"),
    ("せんざい や やくざい は、しようきげん を かくにんしてから つかう。",
     "せんざい や やくざい は、しようきげん を きにしなくて よい。",
     "きげんぎれ の せんざい は こうか が おちたり、ひんしつ が かわったり する こと が あります。"),
    ("さぎょうちゅう に おおきな おと を たてないよう ちゅういする。",
     "さぎょうちゅう は おおきな おと を たてても かまわない。",
     "りようしゃ の めいわく に ならないよう、しずかに さぎょうする こと が もとめられます。"),
    ("ぬれた ゆか に は、すべりどめ の かんばん を おく。",
     "ぬれた ゆか に は なにも おかなくて よい。",
     "てんとうじこ を ふせぐ ため に、ちゅうい かんばん を たてます。"),
    ("せいそう の あと は、つかった せんざい の りょう を かくにんする。",
     "せいそう の あと は、せんざい の りょう を かくにんしなくて よい。",
     "せんざい の ほじゅう や かんり の ため に、つかった りょう を はあくして おきます。"),
    ("しごとちゅう に たいちょう が わるく なったら、むりせず やすむ。",
     "しごとちゅう に たいちょう が わるくても、さいごまで がまんして つづける。",
     "むり を すると じこ や びょうき の げんいん に なる ため、たいちょう が わるい とき は やすみます。"),
    ("せいそう の ぷろ は、みえない ばしょ も ていねいに そうじする。",
     "せいそう の ぷろ は、みえる ばしょ だけ そうじすれば よい。",
     "みえない ばしょ まで ていねいに そうじする こと が、ぷろ として の しごと の しつ を たかめます。"),
    ("といれっとぺーぱー など の びひん は、きれた とき すぐ わかるよう かくにんする。",
     "といれっとぺーぱー など の びひん は、きれても きにしなくて よい。",
     "りようしゃ が こまらないよう、びひん の のこり を こまめに かくにんします。"),
    ("せんざい の ぼとる に は、なかみ が わかるよう ひょうじ を する。",
     "せんざい の ぼとる に は、なかみ が わからなくても よい。",
     "ひょうじ が ないと まちがえて つかう きけん が ある ため、かならず なかみ を ひょうじします。"),
]


def _endless_shuffle(items):
    """items を シャッフルして じゅんばんに かえす。ひとまわり したら もういちど シャッフルする。
    ひとまわり する まで おなじ ようそは でてこない。"""
    while True:
        pool = list(items)
        random.shuffle(pool)
        for it in pool:
            yield it


def build_tool_question(qnum, tool_cycle):
    tool, purpose = next(tool_cycle)
    is_true = random.random() < 0.5
    if is_true:
        chosen_purpose = purpose
    else:
        others = [p for (t, p) in TOOLS if t != tool]
        chosen_purpose = random.choice(others)
    text = "{} は {} どうぐ で ある。".format(tool, chosen_purpose)
    kaisetsu = "{} は「{}」ための どうぐです。".format(tool, purpose)
    return {
        "num": qnum, "text": text, "romaji": sentence_to_romaji(text),
        "answer": is_true, "kaisetsu": kaisetsu, "genre": "どうぐ",
    }


def build_detergent_question(qnum, dirt_cycle):
    dirt, correct_type = next(dirt_cycle)
    is_true = random.random() < 0.5
    chosen_type = correct_type if is_true else random.choice(
        [t for t in DETERGENT_TYPES if t != correct_type])
    text = "{} は {} の せんざい で おとす。".format(dirt, chosen_type)
    kaisetsu = "{} は {} の せんざい で おとします。".format(dirt, correct_type)
    return {
        "num": qnum, "text": text, "romaji": sentence_to_romaji(text),
        "answer": is_true, "kaisetsu": kaisetsu, "genre": "せんざい",
    }


def build_static_question(qnum, static_cycle):
    true_text, false_text, kaisetsu = next(static_cycle)
    is_true = random.random() < 0.5
    text = true_text if is_true else false_text
    return {
        "num": qnum, "text": text, "romaji": sentence_to_romaji(text),
        "answer": is_true, "kaisetsu": kaisetsu, "genre": "まなー・あんぜん",
    }


def generate_questions(count, seed=None):
    if seed is not None:
        random.seed(seed)
    static_cycle = _endless_shuffle(STATIC_FACTS)
    tool_cycle = _endless_shuffle(TOOLS)
    dirt_cycle = _endless_shuffle(DIRTS)

    questions = []
    for i in range(1, count + 1):
        # static facts is the largest, most reliable bank -> weight it higher
        roll = random.random()
        if roll < 0.45:
            q = build_static_question(i, static_cycle)
        elif roll < 0.75:
            q = build_tool_question(i, tool_cycle)
        else:
            q = build_detergent_question(i, dirt_cycle)
        q["num"] = i
        questions.append(q)
    return questions


# ============================================================
# HTML しゅつりょく
# ============================================================
HTML_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>予想問題（自動生成）</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{
  --bg:#f6f3ec; --surface:#ffffff; --surface-2:#eee9dc; --ink:#25302c; --ink-dim:#5b665f;
  --line:#dcd5c3; --primary:#1f5c56; --primary-ink:#eef7f4; --accent:#d98c2b;
  --good:#2f7d4f; --good-bg:#e4f3e8; --bad:#b5432f; --bad-bg:#fbe8e3;
}}
*{{box-sizing:border-box;}}
body{{background:var(--bg); color:var(--ink); font-family:"Yu Gothic","Meiryo",sans-serif; margin:0; padding:20px 16px 40px; display:flex; justify-content:center;}}
.app{{width:100%; max-width:640px; display:flex; flex-direction:column; gap:16px;}}
.masthead{{padding:18px 20px; background:linear-gradient(135deg,var(--primary),#123f3a); color:var(--primary-ink); border-radius:16px;}}
.masthead h1{{margin:0; font-size:18px;}}
.masthead p{{margin:4px 0 0; font-size:12px; opacity:.85;}}
.card{{background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:20px;}}
.progress-wrap{{display:flex; align-items:center; gap:10px; font-size:13px; color:var(--ink-dim);}}
.progress-bar{{flex:1; height:8px; background:var(--surface-2); border-radius:99px; overflow:hidden;}}
.progress-fill{{height:100%; background:var(--primary); border-radius:99px; transition:width .25s;}}
.tag{{display:inline-block; font-size:11px; padding:3px 9px; border-radius:99px; background:var(--surface-2); color:var(--ink-dim); border:1px solid var(--line); margin-top:10px;}}
.q-text{{font-size:19px; line-height:1.75; margin-top:16px;}}
.q-romaji{{font-size:13px; color:var(--ink-dim); margin-top:6px; font-style:italic;}}
.choice-row{{display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:20px;}}
.choice-btn{{cursor:pointer; border-radius:16px; padding:20px 10px; font-size:26px; font-weight:700; border:2px solid var(--line); background:var(--surface-2); color:var(--ink);}}
.choice-btn .label{{display:block; font-size:12px; font-weight:400; color:var(--ink-dim);}}
.choice-btn.maru{{color:var(--primary);}}
.choice-btn.batsu{{color:var(--bad);}}
.choice-btn.correct{{background:var(--good-bg); border-color:var(--good); color:var(--good);}}
.choice-btn.wrong{{background:var(--bad-bg); border-color:var(--bad); color:var(--bad);}}
.choice-btn.dim{{opacity:.5;}}
.feedback{{margin-top:16px; padding:14px 16px; border-radius:12px; font-size:14px; display:none;}}
.feedback.show{{display:block;}}
.feedback.good{{background:var(--good-bg); color:var(--good);}}
.feedback.bad{{background:var(--bad-bg); color:var(--bad);}}
.kaisetsu-box{{margin-top:10px; padding:14px 16px; border-radius:12px; background:var(--surface-2); border:1px dashed var(--line); font-size:13px; line-height:1.7; display:none;}}
.kaisetsu-box.show{{display:block;}}
.kaisetsu-box .head{{font-size:12px; color:var(--accent); font-weight:700; margin-bottom:4px;}}
.next-btn{{margin-top:16px; width:100%; padding:14px; border:none; border-radius:12px; background:var(--primary); color:var(--primary-ink); font-size:15px; font-weight:700; cursor:pointer; display:none;}}
.next-btn.show{{display:block;}}
.score-hero{{text-align:center; padding:20px;}}
.score-num{{font-size:46px; color:var(--primary); font-weight:700;}}
.score-num span{{font-size:20px; color:var(--ink-dim);}}
.btn{{flex:1; padding:13px; border-radius:12px; text-align:center; cursor:pointer; font-size:14px; border:1px solid var(--line); background:var(--surface-2); color:var(--ink);}}
.btn.primary{{background:var(--primary); color:var(--primary-ink); border:none;}}
.btn-row{{display:flex; gap:10px; margin-top:18px;}}
footer{{text-align:center; font-size:11px; color:var(--ink-dim);}}
[hidden]{{display:none!important;}}
</style>
</head>
<body>
<div class="app">
  <div class="masthead">
    <h1>ビルクリーニング基礎級 予想問題（自動生成）</h1>
    <p>生成日時: {generated_at} ／ 全{count}問（オフライン・ランダム生成 / AIによる予想問題です）</p>
  </div>

  <section id="screen-quiz" class="card">
    <div class="progress-wrap">
      <span id="progress-label">1 / {count}</span>
      <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
      <span id="score-label">◎ 0</span>
    </div>
    <span class="tag" id="q-genre-tag"></span>

    <p class="q-text" id="q-text"></p>
    <p class="q-romaji" id="q-romaji"></p>

    <div class="choice-row">
      <button class="choice-btn maru" id="btn-maru">○<span class="label">ただしい</span></button>
      <button class="choice-btn batsu" id="btn-batsu">×<span class="label">あやまり</span></button>
    </div>

    <div class="feedback" id="feedback"></div>
    <div class="kaisetsu-box" id="kaisetsu-box">
      <div class="head">かいせつ Kaisetsu</div>
      <div id="kaisetsu-text"></div>
    </div>

    <button class="next-btn" id="btn-next">つぎへ →</button>
  </section>

  <section id="screen-result" class="card" hidden>
    <div class="score-hero">
      <div class="score-num"><span id="result-correct">0</span><span>/{count}</span></div>
      <p id="result-msg" style="color:var(--ink-dim);"></p>
    </div>
    <div class="btn-row">
      <div class="btn primary" id="btn-restart">もういちど（この問題セット）</div>
    </div>
  </section>

  <footer>このページは自動生成された予想問題です。過去問の正式な内容とは異なります。<br>新しい問題セットが欲しいときは generate_yosou_mondai.py をもう一度実行してください。</footer>
</div>

<script>
var QUESTIONS = {questions_json};
var state = {{pos:0, correct:0, answered:false}};
function byId(id){{return document.getElementById(id);}}
function render(){{
  var q = QUESTIONS[state.pos];
  byId("progress-label").textContent = (state.pos+1) + " / " + QUESTIONS.length;
  byId("progress-fill").style.width = (state.pos/QUESTIONS.length*100) + "%";
  byId("score-label").textContent = "◎ " + state.correct;
  byId("q-genre-tag").textContent = q.genre;
  byId("q-text").textContent = q.text;
  byId("q-romaji").textContent = q.romaji;
  var maru = byId("btn-maru"), batsu = byId("btn-batsu");
  [maru,batsu].forEach(function(b){{ b.disabled=false; b.classList.remove("correct","wrong","dim"); }});
  byId("feedback").classList.remove("show","good","bad");
  byId("kaisetsu-box").classList.remove("show");
  byId("btn-next").classList.remove("show");
  state.answered = false;
}}
function answer(choice){{
  if(state.answered) return;
  state.answered = true;
  var q = QUESTIONS[state.pos];
  var isCorrect = (choice === q.answer);
  var maru = byId("btn-maru"), batsu = byId("btn-batsu");
  var chosen = choice ? maru : batsu, other = choice ? batsu : maru;
  if(isCorrect){{ chosen.classList.add("correct"); state.correct++; }}
  else{{ chosen.classList.add("wrong"); (q.answer?maru:batsu).classList.add("correct"); other.classList.add("dim"); }}
  maru.disabled = true; batsu.disabled = true;
  var fb = byId("feedback");
  fb.classList.add("show", isCorrect?"good":"bad");
  fb.textContent = (isCorrect ? "せいかい！" : "ざんねん…") + " こたえ: " + (q.answer ? "○ ただしい" : "× あやまり");
  byId("kaisetsu-text").textContent = q.kaisetsu;
  byId("kaisetsu-box").classList.add("show");
  byId("score-label").textContent = "◎ " + state.correct;
  byId("progress-fill").style.width = ((state.pos+1)/QUESTIONS.length*100) + "%";
  byId("btn-next").classList.add("show");
}}
function next(){{
  state.pos++;
  if(state.pos >= QUESTIONS.length){{
    byId("screen-quiz").hidden = true;
    byId("screen-result").hidden = false;
    byId("result-correct").textContent = state.correct;
    var pct = Math.round(state.correct/QUESTIONS.length*100);
    var msg = pct===100 ? "パーフェクト！" : pct>=80 ? "よく できました！" : pct>=60 ? "もう すこし！" : "もういちど 練習しましょう。";
    byId("result-msg").textContent = msg;
  }} else {{
    render();
  }}
}}
byId("btn-maru").addEventListener("click", function(){{ answer(true); }});
byId("btn-batsu").addEventListener("click", function(){{ answer(false); }});
byId("btn-next").addEventListener("click", next);
byId("btn-restart").addEventListener("click", function(){{
  state = {{pos:0, correct:0, answered:false}};
  byId("screen-result").hidden = true;
  byId("screen-quiz").hidden = false;
  render();
}});
render();
</script>
</body>
</html>
"""


def render_html(questions):
    data = [{"text": q["text"], "romaji": q["romaji"], "answer": q["answer"],
             "kaisetsu": q["kaisetsu"], "genre": q["genre"]} for q in questions]
    return HTML_TEMPLATE.format(
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        count=len(questions),
        questions_json=json.dumps(data, ensure_ascii=False, indent=2),
    )


def render_text(questions):
    lines = []
    lines.append("ビルクリーニング基礎級 予想問題（自動生成） - {}問".format(len(questions)))
    lines.append("生成日時: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("=" * 50)
    for q in questions:
        lines.append("")
        lines.append("{}. [{}] {}".format(q["num"], q["genre"], q["text"]))
        lines.append("   " + q["romaji"])
        lines.append("   こたえ: " + ("○ ただしい" if q["answer"] else "× あやまり"))
        lines.append("   かいせつ: " + q["kaisetsu"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="ビルクリーニング基礎級 予想問題 自動生成ツール")
    parser.add_argument("--count", type=int, default=20, help="生成する問題数（既定: 20）")
    parser.add_argument("--seed", type=int, default=None, help="乱数シード（指定すると同じ問題セットを再現できます）")
    parser.add_argument("--out-dir", type=str, default=None, help="出力先フォルダ（既定: このスクリプトと同じ場所）")
    parser.add_argument("--no-open", action="store_true", help="生成後にブラウザで自動的に開かない")
    parser.add_argument("--txt", action="store_true", help="テキスト版も出力する")
    args = parser.parse_args()

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    questions = generate_questions(args.count, seed=args.seed)

    html_path = os.path.join(out_dir, "予想問題_さいしん.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(render_html(questions))
    print("HTML を さくせいしました:", html_path)

    if args.txt:
        txt_path = os.path.join(out_dir, "予想問題_さいしん.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(render_text(questions))
        print("テキストを さくせいしました:", txt_path)

    if not args.no_open:
        opened = False
        try:
            if hasattr(os, "startfile"):
                os.startfile(html_path)  # Windows: 既定のブラウザで確実にひらく
                opened = True
        except Exception as e:
            print("os.startfile での起動に しっぱいしました:", e)
        if not opened:
            try:
                import pathlib
                webbrowser.open(pathlib.Path(html_path).resolve().as_uri())
                opened = True
            except Exception as e:
                print("ブラウザでの じどうひょうじに しっぱいしました:", e)
        if not opened:
            print("したの ファイルを てどうで ダブルクリックして ひらいてください:")
            print(" ", html_path)


if __name__ == "__main__":
    main()
