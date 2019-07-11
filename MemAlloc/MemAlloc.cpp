// A simple program that loads a passed file into RAM as many times
// as the file can be fit, then deallocates the memory
//
// I am still working on a few things, including maybe doing RAM
// overwriting with zeroes, so that it adds even more access activity

#include <stdio.h>
#include <stdlib.h>
#include <sys/sysinfo.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>

void handle(int a){
	printf("Caught CTRL-c event. Closing program...\n");
	exit(0);
}

struct fileInfo {
    /* Used to store file size and name */
	unsigned long filesize;
	char* fileptr;
};

struct fileInfo do_alloc(char* filename){
    /* Function that actually does the memory allocation 
     * Returns a fileInfo structure*/

	FILE *f = fopen(filename, "rb");

    // gets file size
	fseek(f, 0, SEEK_END);
	unsigned long fsize = ftell(f); 
	fseek(f, 0, SEEK_SET);

    // allocates the memory chunk and reads in file data
	char* string = (char *) malloc(fsize + 1);
	fread(string, 1, fsize, f);
	fclose(f);

    // generates the structure
	struct fileInfo fs;
	fs.filesize = fsize;
	fs.fileptr = string;

	return fs;

}

int main(int argc, char** argv){

	// initialize signal handlers
	struct sigaction sigIntHandler;
	struct sigaction sigTermHandler;


	sigIntHandler.sa_handler = handle;
   	sigemptyset(&sigIntHandler.sa_mask);
   	sigIntHandler.sa_flags = 0;

	sigTermHandler.sa_handler = handle;
	sigemptyset(&sigTermHandler.sa_mask);
	sigTermHandler.sa_flags = 0;

   	sigaction(SIGINT, &sigIntHandler, NULL);
	sigaction(SIGTERM, &sigTermHandler, NULL);


	int ret = 0;

    // used to find available RAM size left on the machine
	struct sysinfo s;
	unsigned long initRam;

	char* filename = argv[1];
	struct fileInfo f;

	// array to hold all returned fileInfo structures
	struct fileInfo arr[1000];

	// counter
	int ctr = 0;

	bool full;



	// checks if passed a file
	if (argc != 3){
		printf("Usage: %s <file> <num loops>\n", argv[0]);
		return 1;
	}
    	
	int totalNum = atoi(argv[2]);
	int count = 0;
		
	while(count < totalNum){
		
		ret = sysinfo(&s); 
		
		initRam = s.freeram;
    	
		printf("Current available system RAM: %lu\n", initRam);

		
		printf("Beginning memory allocation of file \"%s\"\n", filename);
	
    	// fileInfo structure used to store do_alloc() return
		
		printf("Memory size after file allocation: %lu\n", s.freeram);

		full = false;

		while(s.freeram > f.filesize){
			if (ctr == (sizeof(arr)/ sizeof(*arr))){
				printf("Array full. Stopping memory allocation.\n");
				full = true;
				break;
			}
		
        	printf("Enough memory to allocate another file (%lu free vs %lu filesize). Doing now...\n", s.freeram, f.filesize);
		
			f = do_alloc(filename);
			arr[ctr] = f;

        	ctr++;
			ret = sysinfo(&s);
		}

		if(!full){
			printf("Too little memory to allocate another file (%lu free vs %lu filesize). Not doing\n", s.freeram, f.filesize);
		}

		ret = sysinfo(&s);
		printf("Available system RAM after allocation: %lu\n", s.freeram);

		printf("Accocation complete. Freeing memory\n");
	
		for(int index = 0; index < ctr; index++){
			free(arr[index].fileptr);
		}

		ctr = 0;
		count++;
	}

	return 0;
}
