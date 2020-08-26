#include <stdio.h>
#include <wiringPi.h>
#include <curl/curl.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define PIR1 4
#define PIR2 5
int counter = 0;

char* timeToString(struct tm *t) {
	static char s[20];

    sprintf(s, "%04d-%02d-%02d-%02d-%02d-%02d",
    	    t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
		    t->tm_hour + 8, t->tm_min, t->tm_sec);
	return s;
}

// In delay 1second loop
int timer(int minute)			
{
	return 60 * minute;
}
void curl_test(char* data)
{
	CURL *curl;
	CURLcode res;

	curl = curl_easy_init();

	struct curl_slist *list = NULL;
			  
	if(curl) {
		curl_easy_setopt(curl, CURLOPT_URL, "http://bnrtracker.dreammug.com/_API/saveDataFromString.php");
		// curl_easy_setopt(curl, CURLOPT_URL, "http://54.180.83.60:8000");
		curl_easy_setopt(curl, CURLOPT_POST, 1L); //POST option
		curl_easy_setopt(curl, CURLOPT_POSTFIELDS,data);

		res = curl_easy_perform(curl); 
		curl_slist_free_all(list); // C

		if(res != CURLE_OK){
			printf("curl_easy_perform() failed: %s\n",curl_easy_strerror(res));
		}   
		else{
			printf("\ndata connect success!\n");
		}   
		curl_easy_cleanup(curl); // curl_easy_init
	}
}

void send_data()
{
	struct tm *t;
	time_t timer;

    timer = time(NULL);
    t = localtime(&timer);
    FILE * fp; 
    fp = fopen("k.json","w+");
				    
    fprintf(fp, "isRegularData=true&dataString=");
	fprintf(fp, "[");
	fprintf(fp, "{");
	fprintf(fp, "\"tra_lat\": \"%s\",", "*****");
	fprintf(fp, "\"tra_lon\": \"%s\",", "*****");
	fprintf(fp, "\"tra_temp\": \"%d\",", counter);
	fprintf(fp, "\"tra_datetime\": \"%s\",", timeToString(t));
	fprintf(fp, "\"de_number\": \"%s\"", "legaro_proto5");
	fprintf(fp, "}");
	fprintf(fp, "]");

	char *buffer;
	int size;
	int number;

	fseek(fp, 0, SEEK_END);
	size = ftell(fp);

	buffer = malloc(size + 1); 
	memset(buffer, 0, size + 1); 

	fseek(fp, 0, SEEK_SET);
	number = fread(buffer, size, 1, fp);

	curl_test(buffer);
	
	fclose(fp);
	printf("\n");
	printf("%s\n", buffer);
	free(buffer);
}

int main()
{
	if(wiringPiSetup() == -1) return 1;
	int timeflow = 0;
	pinMode(PIR1,INPUT);
	pinMode(PIR2,INPUT);
	while(1)
	{
		timeflow++;
		if(digitalRead(PIR1) == 1 && digitalRead(PIR2) == 1)
		{
			counter++;
			printf("detection\n");
		}
		else printf("Not Detected\n");
		
		delay(1000);
		timerflow++;
		if(timerflow == timer(5))
		{	
			send_data(counter);
			counter = 0;
		}
	}
	return 0;
}
