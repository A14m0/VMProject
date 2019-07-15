#include "header.h"

std::ofstream file;

class Network
{
private:
	int sockfd, portno, n, ret;
	struct sockaddr_in serv_addr;
    struct hostent *server;
	bool isActive;
	
	
public:
	Network(const char*, int);
	Network(bool);
	void Connect(int);
	bool IsActive(bool);
	~Network();
};


void handle(int a);
int cpu_calc(int n);
int memory_alloc_speed(int repeat);
void error(const char *msg);
int net_speed(Network* net, int num);
int speed_test(int function);
void write_data(char* name, int n, int s, int t, int u);
void write_header();
bool DirectoryExists( const char* pzPath );



Network::Network(const char* host, int port){
	/*Primary constructor for initializing connection information */
	serv_addr.sin_family = AF_INET; 
	serv_addr.sin_port = htons(port);

	
	if(inet_pton(AF_INET, host, &serv_addr.sin_addr) <= 0)
		printf("[-] ERROR invalid address\n");

    portno = port;   
}

Network::Network(bool opt){
	/*Dummy constructor for passing false network classes to switch loop */
	isActive = opt;
}

bool Network::IsActive(bool opt){
	/*Accessor method for server alive state */
	return opt;
}

void Network::Connect(int counter){
	/*Handles network connection to testing server */

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	
    if (sockfd < 0) 
        error("ERROR opening socket");
	
	ret = connect(sockfd,(struct sockaddr *) &serv_addr,sizeof(serv_addr));
	if (ret < 0) 
        error("ERROR connecting");

	int count = 0;
	char buffer[256] = "SuperDuperStressTest";
    

    while(count < counter){
        n = send(sockfd,buffer,strlen(buffer), MSG_NOSIGNAL);
		
		if (n < 0) 
            error("ERROR writing to socket");
        
        bzero(buffer,256);
        n = read(sockfd,buffer,255);
        if (n < 0) 
            error("ERROR reading from socket");

		count++;
    }
    

}

Network::~Network()
{
	close(sockfd);
}


void handle(int a){
	/*Catches system signals */
	std::cout << "Caught system termination signal. Closing program..." << std::endl;
	file.close();
	exit(0);
}

void error(const char *msg){
	/*Writes error message and quits */
    perror(msg);
    exit(0);
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

int net_speed(Network net, int num){
	/*Handles network connection test loop */
	net.Connect(num);
    return 0;
}


int speed_test(int function, Network net){
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
	case NET_CHECK:
		net_speed(net, 50);
		break;
	default:
		printf("ERROR not passed correct value\n");
		break;
	}
	
	int second_clock = clock();
	
	int diff = second_clock - first_clock;
	
	return diff;
}

void write_data(char* name, int n, int s, int t, int u){
	/*Writes passed averages to file */
	time_t now = time(0);
   
   	// convert now to string form
   	std::string dt(ctime(&now));

	dt.erase(std::remove(dt.begin(), dt.end(), '\n'), dt.end());

	file << dt << "," << name << "," << n << ","<<  s << "," << t << "," << u << std::endl;
}

void write_header(){
	/*Writes CSV header to file */
	file << "Date/Time,VM name,Number VMs,CPU time,Mem access time,Net time\n";
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



int main(int argc, char** argv){

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
	Network net("172.16.193.1", 13337);

	time_t now = time(0);
	std::string dt(ctime(&now));
	dt.erase(std::remove(dt.begin(), dt.end(), '\n'), dt.end());

    // opens .CSV file
	dt = "data/" + dt + ".csv";
	file.open(dt.c_str(), std::ios::app);
	printf("[i] File opened: %s\n", dt.c_str());

    // writes header
	write_header();

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

	int diffcpu = 0, diffmem = 0, ctr = 0, diffnet = 0;
	time_t start, end;//CPU, endCPU, startMEM, endMEM, startNET, endNET;
    double elapsed; 
	Network dummy(false);

	while(true){
		time(&start);
		do {
			time(&end);
			elapsed = difftime(end, start);

			diffcpu += speed_test(CPU_CHECK, dummy);

			diffmem += speed_test(MEM_CHECK, dummy);
			
			diffnet += speed_test(NET_CHECK, net);
			
			ctr++;
		} while(elapsed < 1);
		printf("Number of individual checks in 1 second: %d\n", ctr);

		write_data(name, numVM, diffcpu/ctr, diffmem/ctr, diffnet/ctr);
		diffcpu = 0;
		diffmem = 0;
		diffnet = 0;
		ctr = 0;
	}

	
	return 0;

}
