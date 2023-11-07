* Abstract package parsing into a base class and pass that parser to the package reader, in preparation to support additional Brymen meters.

* Eventually it would be good to turn this into a generic Brymen package, supporting the following additional protocols:

 * [BM130 series](https://web.archive.org/web/20231031164042/http://www.brymen.com/images/DownloadList/ProtocolList/BM130_List/BM130-6000-count-LoggerClamp-protocol-1.pdf)
 * [BM150 / BM351 series](https://web.archive.org/web/20231031164121/http://www.brymen.com/images/DownloadList/ProtocolList/BM150-BM351_List/BM150-BM351-6000-count-PowerClamp-protocol-1.pdf)
 * [BM157 / BM357 series](https://web.archive.org/web/20231031164228/http://www.brymen.com/images/DownloadList/ProtocolList/BM157-BM357_List/BM157-BM357-6000-count-3Phase-PowerClamp-protocol.pdf)
 * [BM180 / BM190 series](https://web.archive.org/web/20231031164253/http://www.brymen.com/images/DownloadList/ProtocolList/BM180-BM190_List/BM180-BM190-6000-count-dual-display-clampmeter-protocol.pdf)
 * [BM200 series](https://web.archive.org/web/20181222200618/http://www.brymen.com/images/DownloadList/ProtocolList/BM200_List/BM200-2500-count-DMM-protocol.pdf)
 * [BM510 series](https://web.archive.org/web/20231031164350/http://www.brymen.com/images/DownloadList/ProtocolList/BM510_List/BM510-5000-count-logging-DMM-protocol-for-BC-85X.zip)
 * [BM520 / BM520s series](https://web.archive.org/web/20231031164431/http://www.brymen.com/images/DownloadList/ProtocolList/BM520-BM520s_List/BM520-BM520s-10000-count-professional-dual-display-mobile-logging-DMMs-protocol.zip)
 * [BM810 / BM810a / BM810s series](https://web.archive.org/web/20231031164507/http://www.brymen.com/images/DownloadList/ProtocolList/BM810-BM810a-BM810s_List/BM810-BM810a-BM810s-5000-count-DMM-protocol-BC85X-BC85Xa.zip)
 * [BM820 / BM820s series](https://web.archive.org/web/20231031164537/http://www.brymen.com/images/DownloadList/ProtocolList/BM820-BM820s_List/BM820-BM820s-10000count-professional-dual-display-DMMs-protocol.pdf)
 * [BM850 / BM850a / BM850s series](https://web.archive.org/web/20231031164609/http://www.brymen.com/images/DownloadList/ProtocolList/BM850-BM850a-BM850s_List/BM850-BM850a-BM850s-500000-count-DMM-protocol-BC85X-BC85Xa.zip)
 * [BM860 / BM860s series](https://web.archive.org/web/20191231053213/http://www.brymen.com/images/DownloadList/ProtocolList/BM860-BM860s_List/BM860-BM860s-500000-count-dual-display-DMMs-protocol.pdf) - Unlike the others, which constantly stream data, this one provides readings in response to requests.  It also presents itself as a HID rather than a standard serial port.  See [this project](https://github.com/TheHWcave/BM869S-remote-access) for more details and interim support.

 See [PROTOCOLS.txt](PROTOCOLS.txt) for a quick way to download all of the documentation.  For example:

 ```
wget -c -i PROTOCOLS.txt
```
or

 ```console
curl -R -C - --remote-name-all $(cat PROTOCOLS.txt)
```