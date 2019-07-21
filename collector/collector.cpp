#include "header.h"
#include "ping.h"

std::ofstream file;
std::ofstream netFile;


/*
NOTE TO SELF:
SEE IF IT IS POSSIBLE TO LINK THE NETWORK FILES TO THE MAIN FILE THROUGH SOMETHING???
MAYBE NAME IT AS ONE OF THE HEADER OPTIONS AND JUST LOAD THAT DATA TOO??
 */







static uid_t ruid;

void handle(int a);
int cpu_calc(int n);
int memory_alloc_speed(int repeat);
void error(const char *msg);
//int net_speed();
int speed_test(int function);
void write_data(char* name, int n, int s, int t, int u);
void write_header();
bool DirectoryExists( const char* pzPath );



void handle(int a){
	/*Catches system signals */
	std::cout << "Caught system termination signal. Closing program..." << std::endl;
	file.close();
	netFile.close();
	exit(0);
}

void error(const char *msg){
	/*Writes error message and quits */
    perror(msg);
    exit(0);
}

void do_root (void)
{
        int status;
        status = seteuid (0);
        if (status < 0) { 
        	perror("Failed to set effective UID to root");
			printf("Make sure that this program is owned by root and the setuid bit is set\n");
			printf("This can be done through the following:\n\tsudo chown root collector\n\tsudo chmod 4755 collector\n");
			exit(1);
		}   
}

void undo_root(void){
	int status;
	status = seteuid (ruid);
    if (status < 0) { 
        perror("Failed to set effective UID to non-root user");
    }
}


int cpu_calc(int n) {
    /*Handles cpu access time speed test loop */

  	int i,j;
  	int freq=n-1;
  	for (i=2; i<=n; ++i) {
		for (j=sqrt(i);j>1;--j){
			if (i%j==0) {
				--freq; 
				break;
			}
		}

  	}
  	return freq;
}


int memory_alloc_speed(int repeat){
	/*Handles memory allocation speed test loop */
	for(int i = 0; i < repeat; i++){
		int* memory = new int; // allocates a chunk of memory...
		delete memory; // and then frees it
	}

	return 0;
}

void net_write_headers(){
	netFile << "Date,gateway,time\n";
}

void net_write(long double *vals, char *addr){
	time_t now = time(0);
  	std::string dt(ctime(&now));
	dt.erase(std::remove(dt.begin(), dt.end(), '\n'), dt.end());


	for (size_t i = 0; i < PING_NUM; i++)
	{
		netFile << dt << "," << addr << "," << vals[i] << "\n";
		
	}	
}

void *netTest(void *data){
	char *addr = (char *) data;
	long double *vals;
	
	net_write_headers();
	
	while(1){
		do_root();
		vals = ping(addr);
		undo_root();
	
		net_write(vals, addr);
	
		sleep(300);
	}
	
}


int speed_test(int function){
	/*Manages which functions get called */

	int x;

	int first_clock = clock();
	
	switch (function)
	{
	case CPU_CHECK:
		cpu_calc(9999);
		break;
	case MEM_CHECK:
		memory_alloc_speed(99999);
		break;
	default:
		printf("ERROR not passed correct value\n");
		break;
	}
	
	int second_clock = clock();
	
	int diff = second_clock - first_clock;
	
	return diff;
}

void write_data(char* name, int n, int s, int t){
	/*Writes passed averages to file */
	time_t now = time(0);
   
   	// convert now to string form
   	std::string dt(ctime(&now));

	dt.erase(std::remove(dt.begin(), dt.end(), '\n'), dt.end());

	file << dt << "," << name << "," << n << ","<<  s << "," << t << std::endl;
}

void write_header(){
	/*Writes CSV header to file */
	file << "Date/Time,VM name,Number VMs,CPU time,Mem access time\n";
}

bool DirectoryExists( const char* pzPath )
{
	/*Tests if a directory exists in the file system */
    if ( pzPath == NULL) return false;

    DIR *pDir;
    bool bExists = false;

    pDir = opendir (pzPath);

    if (pDir != NULL)
    {
        bExists = true;    
        (void) closedir (pDir);
    }

    return bExists;
}

int index_of(char* str, char find){
    int i = 0;
 
    while (str[i] != '\0')
    {
        if (str[i] == find)
        {
            return i;
        }

        i++;
    }

    return -1;

}




int main(int argc, char** argv) {
	// saves the user's UID to drop privilages when needed
	ruid = getuid();

    // initializes signal handlers
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

	// gets current file path, so data will be written to correct folder regardless of where execution is called
	char result[4096];
	memset(result, 0, sizeof(result));
	ssize_t count = readlink( "/proc/self/exe", result, 4096);

	char dir[4096];
	memset(dir, 0, sizeof(dir));
	char* last;
	last = strrchr(result, '/');

	unsigned long index = last - result;
	strncpy(dir, result, index);
	
	printf("[i] Determined directory: %s\n", dir);
	
	int ret = chdir(dir);


	if(ret < 0){
		perror("[-] Failed to change directory");
		exit(-1);
	}

	if(!DirectoryExists("data")){
		printf("Adding directory...\n");
		mkdir("data", S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
	}

    // initialize variables
	char* name = "BASELINE (no vm)";
	int numVM = 0;
	char yesNo = 'a';
	time_t now = time(0);
	std::string dt(ctime(&now));
	std::string nfd;
	dt.erase(std::remove(dt.begin(), dt.end(), '\n'), dt.end());
	


    // opens .CSV file
	nfd = "data/netDat_" + dt + ".csv";
	dt = "data/mainDat_" + dt + ".csv";
	file.open(dt.c_str(), std::ios::app);
	file.open(nfd.c_str(), std::ios::app);
	printf("[i] File opened: %s\n", dt.c_str());

    // writes header
	write_header();


	// Get input if command args arent passed
	if(argc != 3){
		std::cout << "Is a Virtual Machine running? (y/n) >> ";
		std::cin >> yesNo;
	
		if(yesNo == 'y' || yesNo == 'Y'){
			std::cout << "Enter VM name >> ";
			char name2[64];
			std::cin >> name2; // <-- Fix this. needs to be buffered into memory, then set name to the ptr to that mem
			name = name2;

			std::cout << "Number of VMs? >> ";
			std::cin >> numVM;

		}

		
		std::cout << "Beginning...\n";

	} else {
		name = argv[1];
		numVM = atoi(argv[2]);
		std::cout << "Beginning...\n";
	}


/////// GET GATEWAY ADDRESS ///////
	FILE* comm_out;
	comm_out = popen("traceroute google.com", "r");
	char comm_buffer[4096];
	int i = 0;

	while(i < 3){
		fgets(comm_buffer, sizeof(comm_buffer), comm_out);
		i++;
	}

	int ending_space = index_of(comm_buffer+4, ' ');

	char ip[4096];
	strncpy(ip, comm_buffer+4, ending_space -4);
	printf("[i] Determined IP of gateway: %s\n", ip);

	fclose(comm_out);

/////// comm_buffer should only contain the line we want now //////

	
	int diffcpu = 0, diffmem = 0, ctr = 0;
	time_t start, end;
    double elapsed; 

	pthread_t nettestThread;

	if(pthread_create(&nettestThread, NULL, netTest, ip)){
		perror("Failed to create thread");
		exit(1);
	}


/////// Primary loop ///////
	while(true){
		time(&start);
		do {
			time(&end);
			elapsed = difftime(end, start);

			diffcpu += speed_test(CPU_CHECK);

			diffmem += speed_test(MEM_CHECK);
			
			ctr++;
		} while(elapsed < 1);
		printf("Number of individual checks in 1 second: %d\n", ctr);

		write_data(name, numVM, diffcpu/ctr, diffmem/ctr);
		diffcpu = 0;
		diffmem = 0;
		ctr = 0;
	}

	
	return 0;

}




/*
TODOS: Trash the Network testing information stuffs...
	   Implement 2 different things:
			1) Traceroute
			2) Ping the second hop to, say, google.com (note only do one per sec (not avg), do once a sec 15 times, then wait 5 mins)


https://stackoverflow.com/questions/15458438/implementing-traceroute-using-icmp-in-c#15462552
https://gist.github.com/KelviNosse/930988c7dda1966e164a712fa32dc567
*/