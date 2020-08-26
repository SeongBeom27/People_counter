URL = "target_url"
json_data = {}

def send_data(val):
    now = time.localtime()
    datetime = time.strftime('%Y-%m-%d-%H-%M', now)

    json_data["isRegularData"] = True
    json_data["dataString"] = []
    json_data["dataString"].append({
            "tra_lat":"*****",
            "tra_lon":"*****",
            "tra_datetime":datetime,
            "tra_temp":str(val),
            "de_number":"legaro_proto4"})

    #로그용으로 사용
    with open("./sample.json", 'w') as outfile:
        json.dump(json_data, outfile)
    print(json_data)

    #호출 결과를 result에 담는다.
    result = requests.post(DREAMUG_URL, data=json.dumps(json_data))

    #드림머그 서버가 응답한 값 : 정상이면 {"status_code":"0","message":"Success","result":넘긴targetdata} 반환
    # 만약 result에 null이 찍히면 값이 제대로 안 넘어간 것
    #result.json으로 써도되기는 한데 서버가 이상해서 json으로 안뱉을까봐 그냥 text로 사용
    #result로 찍어볼 수 있는 다양한 값들 참고
    #https://dgkim5360.tistory.com/entry/python-requests 여기서 4번 참고
    print(result.text)