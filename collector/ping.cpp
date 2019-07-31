#include "ping.h"

#include <fcntl.h>
#include <errno.h>
#include <sys/socket.h>
#include <resolv.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/ip_icmp.h>
#include <unistd.h>
#include <sys/types.h>
#include <strings.h>
#include <time.h> 
//#include <fcntl.h> 


#define PACKETSIZE  64
struct packet
{
    struct icmphdr hdr;
    char msg[PACKETSIZE-sizeof(struct icmphdr)];
};

int pid=-1;
struct protoent *proto = NULL;
int cnt=1;

/*--------------------------------------------------------------------*/
/*--- checksum - standard 1s complement checksum                   ---*/
/*--------------------------------------------------------------------*/
unsigned short checksum(void *b, int len)
{
    unsigned short *buf = (unsigned short *) b;
    unsigned int sum=0;
    unsigned short result;

    for ( sum = 0; len > 1; len -= 2 )
        sum += *buf++;
    if ( len == 1 )
        sum += *(unsigned char*)buf;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    result = ~sum;
    return result;
}


/*--------------------------------------------------------------------*/
/*--- ping - Create message and send it.                           ---*/
/*    return 0 is ping Ok, return 1 is ping not OK.                ---*/
/*--------------------------------------------------------------------*/
long double ping(char *address)
{
    const int val=255;
    int i, sd;
    struct packet pckt;
    struct sockaddr_in r_addr;
    int loop;
    struct hostent *hname;
    struct sockaddr_in addr_ping,*addr;
    long double rtt_msec;


    struct timespec time_start, time_end, tfs, tfe;

    clock_gettime(CLOCK_MONOTONIC, &tfs); 


    pid = getpid();
    proto = getprotobyname("ICMP");
    hname = gethostbyname(address);
    bzero(&addr_ping, sizeof(addr_ping));
    addr_ping.sin_family = hname->h_addrtype;
    addr_ping.sin_port = 0;
    addr_ping.sin_addr.s_addr = *(long*)hname->h_addr;

    addr = &addr_ping;

    sd = socket(PF_INET, SOCK_RAW, proto->p_proto);
    if ( sd < 0 )
    {
        perror("socket");
        return NULL;
    }
    if ( setsockopt(sd, SOL_IP, IP_TTL, &val, sizeof(val)) != 0)
    {
        perror("Set TTL option");
        return NULL;
    }
    if ( fcntl(sd, F_SETFL, O_NONBLOCK) != 0 )
    {
        perror("Request nonblocking I/O");
        return NULL;
    }

    int len = 0;
    double timeElapsed = 0;
    bzero(&pckt, sizeof(pckt));
    pckt.hdr.type = ICMP_ECHO;
    pckt.hdr.un.echo.id = pid;
        
    for ( i = 0; i < sizeof(pckt.msg)-1; i++ )
        pckt.msg[i] = i+'0';       
       
    pckt.msg[i] = 0;
    pckt.hdr.un.echo.sequence = cnt++;
    pckt.hdr.checksum = checksum(&pckt, sizeof(pckt));


///////////// CHECK LINE 218 /////////////////

    clock_gettime(CLOCK_MONOTONIC, &time_start); 
	
    if ( sendto(sd, &pckt, sizeof(pckt), 0, (struct sockaddr*)addr, sizeof(*addr)) <= 0 )
        perror("sendto");

    len=sizeof(r_addr);

    if ( recvfrom(sd, &pckt, sizeof(pckt), 0, (struct sockaddr*)&r_addr, &len) > 0 )
    {
        printf("Failed recvfrom\n");
     	return NULL;
    }

    clock_gettime(CLOCK_MONOTONIC, &time_end); 

    timeElapsed = ((double)(time_end.tv_nsec - time_start.tv_nsec))/1000000.0;
    rtt_msec = (time_end.tv_sec- time_start.tv_sec) * 100000.0 + timeElapsed; 
			

    printf("%s: Got time %Lf\n", address, rtt_msec);	

    return rtt_msec;
}


