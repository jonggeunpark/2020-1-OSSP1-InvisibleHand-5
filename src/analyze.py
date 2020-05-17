# -*- coding: utf-8 -*-
import nltk
import create
import pandas as pd
import grammar
import morphs

# 감정 사전에서 단어 찾기
def find_word(emotion_dictionary_lists, token):
    for emo in emotion_dictionary_lists:
        if token[0] in emo.keys():
            return emo[token[0]]
    return -1, 0  # 단어사전에 없었다면

# 문장 성분 분석
def input_element(df, index, token_list):
    parser = nltk.RegexpParser(grammar.grammar)
    chunks = parser.parse(token_list)
    subject = []
    object = []
    for sub_tree in chunks.subtrees():
        if sub_tree.label() == "주어":
            subject.append(sub_tree[0][0])
        elif sub_tree.label() == "목적어":
            object.append(sub_tree[0][0])
    df.at[index, "주어"] = subject
    df.at[index, "목적어"] = object
    return df

# 감정 분석
def input_emotion_word(df,index, emotion_dictionary_lists, token_list):
    emo_word = []
    for token in token_list:
        word_result = find_word(emotion_dictionary_lists, token)
        if word_result != (-1, 0):  # 문장에서 단어 사전에 있는 단어가 있다면
            emo_word.append(token[0])
            df.at[index, f"{word_result[0]}"] += float(word_result[1])
    df.at[index, "감정 단어"] = emo_word
    return df

# 화자 분석
def input_character(df, index, listOfCharacter, token_list):
    count = [0 for i in range(len(listOfCharacter))]  # 문장 당 등장인물의 출현 횟su

    for token in token_list:
        if token[0] in listOfCharacter:  # 문장에서 등장인물 등장 체크
            count[listOfCharacter.index(token[0])] += 1
    for i, c in enumerate(count):
        if c >= 1:
            df.at[index, "화자"]=[listOfCharacter[i], str(c)]
    return df

def analyze_sentence(df, listOfCharacter, emotion_dictionary_lists, charOfPage):
    page_num = 0
    length = 0
    index = 0

    for line in df["문장"]:
        if(length > charOfPage):
            page_num = page_num + 1
            length = 0
        length = length + len(line)#
        df.at[index, "페이지 번호"] = page_num

        token_list = morphs.tokenizer(line)
        df = input_element(df, index, token_list) #df에 주어,목적어 값 입력
        df = input_emotion_word(df,index,emotion_dictionary_lists,token_list) #df에 감정 단어 및 감정 값 입력
        df = input_character(df,index, listOfCharacter,token_list) #df에 화자 값 입력
        index = index + 1
    return df

def merge_sentence(df_sentence, numOfPage, listOfEmotion, listOfCharacter):
    writer = pd.ExcelWriter("../res/output/등장인물.xlsx", engine='openpyxl')

    df_list_character = []
    df_character = pd.DataFrame(index=range(0, numOfPage), columns=[f"{emotion}" for emotion in listOfEmotion])

    for character in listOfCharacter:
        for num in range(0, numOfPage):
            page_filter = df_sentence['페이지 번호'].isin([num])
            page_filtered_df = df_sentence[page_filter] # num 페이지 행들 추출
            page_filtered_df = page_filtered_df.loc[:, ('기쁨', '슬픔', '분노', '공포', '혐오', '놀람')]  # 추출한 행들의 감정 열 추출
            emotion_sum_df = page_filtered_df.sum(axis=0)  # 감정 별 합 추출
            df_character.loc[num] = emotion_sum_df  # 등장인물 데이터프레임에 감정 별 합 대입
        df_list_character.append(df_character)
        df_character.to_excel(writer, sheet_name=f"{character}")

    writer.save()
    return df_list_character
