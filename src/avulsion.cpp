// Independent implementation from written specifications; no author code used.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
using Matrix = std::array<std::array<double,6>,3>;
const double NaN = std::numeric_limits<double>::quiet_NaN();
const Matrix TM{{{{.2909,.2493,.4806,.5568,.4438,.1706}},
                 {{-.2728,-.2174,-.5508,.7221,.0733,-.1648}},
                 {{.1446,.1761,.3322,.3396,-.6210,-.4186}}}};
const Matrix ETM{{{{.3561,.3972,.3904,.6966,.2286,.1596}},
                  {{-.3344,-.3544,-.4556,.6966,-.0242,-.2630}},
                  {{.2626,.2141,.0926,.0656,-.7629,-.5388}}}};
const Matrix OLI{{{{.3029,.2786,.4733,.5599,.5080,.1872}},
                  {{-.2941,-.2430,-.5424,.7276,.0713,-.1608}},
                  {{.1511,.1973,.3283,.3407,-.7117,-.4559}}}};
const Matrix& coefficients(int sensor) {
 if(sensor==5) return TM;
 if(sensor==7) return ETM;
 if(sensor==8) return OLI;
 throw std::runtime_error("Unknown sensor");
}
std::vector<std::string> split(const std::string& s, char sep=',') {
 std::vector<std::string> v; std::stringstream in(s); std::string x;
 while(std::getline(in,x,sep)) {
  if(!x.empty() && x.back()=='\r') x.pop_back();
  v.push_back(x);
 }
 return v;
}
template<typename T> std::vector<T> read(const fs::path& p, size_t n) {
 std::ifstream f(p,std::ios::binary); if(!f) throw std::runtime_error("Cannot read "+p.string());
 std::vector<T> v(n); f.read(reinterpret_cast<char*>(v.data()),n*sizeof(T));
 if(static_cast<size_t>(f.gcount())!=n*sizeof(T)) throw std::runtime_error("Wrong array length: "+p.string());
 char extra; if(f.read(&extra,1)) throw std::runtime_error("Excess array bytes: "+p.string());
 return v;
}
template<typename T> void write(const fs::path& p,const std::vector<T>& v) {
 std::ofstream f(p,std::ios::binary); if(!f) throw std::runtime_error("Cannot write "+p.string());
 f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));
}
double quantile(std::vector<double> v,double p) {
 v.erase(std::remove_if(v.begin(),v.end(),[](double x){return !std::isfinite(x);}),v.end());
 if(v.empty()) return NaN;
 double h=(v.size()-1)*p; size_t lo=static_cast<size_t>(h),hi=static_cast<size_t>(std::ceil(h));
 std::nth_element(v.begin(),v.begin()+lo,v.end()); double a=v[lo];
 if(lo==hi) return a;
 std::nth_element(v.begin()+lo+1,v.begin()+hi,v.end()); return a+(h-lo)*(v[hi]-a);
}
double median(std::vector<double>& v) {
 if(v.empty()) return NaN;
 size_t k=v.size()/2;
 std::nth_element(v.begin(),v.begin()+k,v.end()); double b=v[k];
 if(v.size()%2) return b;
 return (b+*std::max_element(v.begin(),v.begin()+k))/2.;
}
bool clear(uint16_t qa,uint16_t sat,int sensor) {
 // USGS QA: fill, dilated cloud, cirrus (OLI), cloud, shadow, snow.
 uint16_t invalid=(1u<<0)|(1u<<1)|(1u<<3)|(1u<<4)|(1u<<5);
 if(sensor==8) invalid|=(1u<<2);
 return (qa&invalid)==0 && sat==0;
}
double reflectance(uint16_t dn) {return dn==0?NaN:dn*.0000275-.2;}
std::array<double,3> transform(const std::array<double,6>& r,int sensor) {
 std::array<double,3> t{}; const auto& c=coefficients(sensor);
 for(size_t j=0;j<3;++j) for(size_t b=0;b<6;++b) t[j]+=c[j][b]*r[b];
 return t;
}
struct Grid {size_t width,height; double dx,dy,x0,y0; int epsg; size_t size()const{return width*height;}};
Grid grid(const fs::path& dir) {
 Grid g{}; std::ifstream f(dir/"grid.txt"); f>>g.width>>g.height>>g.dx>>g.dy>>g.x0>>g.y0>>g.epsg;
 if(!f || !g.size() || g.dx<=0 || g.dy>=0) throw std::runtime_error("Invalid grid.txt");
 return g;
}
struct Scene {std::string date,file;int sensor;};
void analyze(const fs::path& input,const fs::path& output) {
 Grid g=grid(input); size_t n=g.size(); fs::create_directories(output);
 fs::copy_file(input/"grid.txt",output/"grid.txt",fs::copy_options::overwrite_existing);
 std::ifstream f(input/"scenes.csv"); if(!f) throw std::runtime_error("Missing scenes.csv");
 std::string line;std::getline(f,line); std::map<int,std::vector<Scene>> years;
 while(std::getline(f,line)) {auto v=split(line);if(v.size()<3)continue;years[std::stoi(v[0].substr(0,4))].push_back({v[0],v[2],std::stoi(v[1])});}
 std::ofstream summary(output/"annual.csv");
 summary<<"year,sensor,available_scenes,used_scenes,valid_pixels,total_pixels,B90,G50,W75,bright_pixels,wet_pixels\n"<<std::setprecision(12);
 std::vector<uint16_t> countB(n,0),countW(n,0),coverage(n,0);
 for(auto& entry:years) {
  int year=entry.first;auto& scenes=entry.second;
  // Avoid applying one sensor's coefficients to another sensor's composite.
  // Written description leaves mixed-sensor annual treatment unspecified.
  std::map<int,uint64_t> clear_observations;
  for(auto&s:scenes) {
   auto r=read<uint16_t>(input/s.file,8*n);uint64_t score=0;
   for(size_t p=0;p<n;++p) {
    if(!clear(r[6*n+p],r[7*n+p],s.sensor))continue;
    bool valid=true;for(size_t b=0;b<6;++b)if(r[b*n+p]==0)valid=false;
    score+=valid;
   }
   clear_observations[s.sensor]+=score;
  }
  int sensor=0;uint64_t best=0;
  for(auto&x:clear_observations)if(x.second>=best){sensor=x.first;best=x.second;}
  std::vector<std::vector<uint16_t>> raw;
  for(auto&s:scenes)if(s.sensor==sensor)raw.push_back(read<uint16_t>(input/s.file,8*n));
  std::vector<float> tc(3*n,static_cast<float>(NaN)),rgb(3*n,static_cast<float>(NaN));
  std::vector<uint16_t> observations(n,0);
  #pragma omp parallel for schedule(static)
  for(int64_t pp=0;pp<static_cast<int64_t>(n);++pp) {
   size_t p=static_cast<size_t>(pp);std::array<std::vector<double>,6> values;
   for(auto&v:values)v.reserve(raw.size());
   for(auto&r:raw) {
    if(!clear(r[6*n+p],r[7*n+p],sensor))continue;
    bool good=true;for(size_t b=0;b<6;++b)if(r[b*n+p]==0)good=false;if(!good)continue;
    for(size_t b=0;b<6;++b) values[b].push_back(reflectance(r[b*n+p]));
   }
   observations[p]=static_cast<uint16_t>(values[0].size());if(!observations[p])continue;
   std::array<double,6> med{};for(size_t b=0;b<6;++b)med[b]=median(values[b]);
   auto t=transform(med,sensor);for(size_t b=0;b<3;++b){tc[b*n+p]=t[b];rgb[b*n+p]=med[2-b];}
  }
  std::array<double,3> q{};const double probs[3]={.90,.50,.75};
  for(size_t b=0;b<3;++b){std::vector<double> v(tc.begin()+b*n,tc.begin()+(b+1)*n);q[b]=quantile(v,probs[b]);}
  std::vector<uint8_t> bmask(n,0),wmask(n,0);size_t valid=0,nb=0,nw=0;
  for(size_t p=0;p<n;++p)if(std::isfinite(tc[p])) {
   ++valid;++coverage[p];bmask[p]=(tc[p]>q[0]&&tc[n+p]<q[1]);wmask[p]=(tc[2*n+p]>q[2]&&tc[n+p]<q[1]);
   countB[p]+=bmask[p];countW[p]+=wmask[p];nb+=bmask[p];nw+=wmask[p];
  }
  std::string prefix=std::to_string(year);
  write(output/(prefix+"_tct.f32"),tc);write(output/(prefix+"_rgb.f32"),rgb);
  write(output/(prefix+"_observations.u16"),observations);
  write(output/(prefix+"_B.u8"),bmask);write(output/(prefix+"_W.u8"),wmask);
  summary<<year<<','<<sensor<<','<<scenes.size()<<','<<raw.size()<<','<<valid<<','<<n<<','<<q[0]<<','<<q[1]<<','<<q[2]<<','<<nb<<','<<nw<<'\n';summary.flush();
  std::cout<<input.filename()<<" "<<year<<": "<<raw.size()<<" scenes, "<<valid<<" valid pixels\n"<<std::flush;
 }
 write(output/"candidate_years_B.u16",countB);write(output/"candidate_years_W.u16",countW);write(output/"coverage_years.u16",coverage);
}
bool inside(double x,double y,const std::vector<std::array<double,2>>& poly) {
 bool c=false;if(poly.size()<3)return false;
 for(size_t i=0,j=poly.size()-1;i<poly.size();j=i++) {
  double xi=poly[i][0],yi=poly[i][1],xj=poly[j][0],yj=poly[j][1];
  if(((yi>y)!=(yj>y)) && (x<(xj-xi)*(y-yi)/(yj-yi)+xi))c=!c;
 }return c;
}
double ratio(size_t a,size_t p){return p?static_cast<double>(a)/p:NaN;}
void measure(const fs::path& processed,const fs::path& annotations,const fs::path& output) {
 fs::create_directories(output);Grid g=grid(processed);size_t n=g.size();
 std::ifstream f(annotations);if(!f)throw std::runtime_error("Independent annotation file is required");
 // Format: role,x_pixel,y_pixel. Roles are parent/avulsion/exclude.
 std::map<std::string,std::vector<std::array<double,2>>> poly;std::string line;std::getline(f,line);
 while(std::getline(f,line)){auto v=split(line);if(v.size()==3)poly[v[0]].push_back({std::stod(v[1]),std::stod(v[2])});}
 if(poly["parent"].size()<3||poly["avulsion"].size()<3)throw std::runtime_error("Both independent channel polygons are required");
 std::ifstream settings(annotations.parent_path()/"years.txt");int p0,p1,a0,a1;
 if(!(settings>>p0>>p1>>a0>>a1)||p0>p1||a0>a1)throw std::runtime_error("Independent parent and event year ranges are required");
 std::ofstream out(output/"measurements.csv");out<<"signature,parent_pixels,avulsion_pixels,parent_area_m2,avulsion_area_m2,SR\n";
 std::vector<uint8_t> parentMask(n,0),avMask(n,0);
 for(size_t p=0;p<n;++p){double x=p%g.width+.5,y=p/g.width+.5;bool excluded=inside(x,y,poly["exclude"]);parentMask[p]=inside(x,y,poly["parent"])&&!excluded;avMask[p]=inside(x,y,poly["avulsion"])&&!excluded;}
 write(output/"parent_mask.u8",parentMask);write(output/"avulsion_mask.u8",avMask);
 size_t smallest=std::numeric_limits<size_t>::max();std::string chosen;double selected=NaN;
 for(auto mode:{std::string("B"),std::string("W")}) {
  std::vector<uint16_t> ap(n,0),pp(n,0);size_t na=0,np=0;int ayears=0,pyears=0;
  for(int yr=std::min(a0,p0);yr<=std::max(a1,p1);++yr){fs::path file=processed/(std::to_string(yr)+"_"+mode+".u8");if(!fs::exists(file))continue;auto v=read<uint8_t>(file,n);bool a=yr>=a0&&yr<=a1,p=yr>=p0&&yr<=p1;ayears+=a;pyears+=p;for(size_t j=0;j<n;++j){if(a&&avMask[j])ap[j]+=v[j];if(p&&parentMask[j])pp[j]+=v[j];}}
  if(!ayears||!pyears)throw std::runtime_error("No acquired images in an annotated time range");
  for(size_t j=0;j<n;++j){na+=ap[j]>0;np+=pp[j]>0;}double sr=ratio(na,np);double area=std::abs(g.dx*g.dy);
  out<<mode<<','<<np<<','<<na<<','<<np*area<<','<<na*area<<','<<sr<<'\n';
  write(output/("fingerprint_"+mode+".u16"),ap);write(output/("parent_"+mode+".u16"),pp);
  if(na<smallest){smallest=na;chosen=mode;selected=sr;}
 }
 std::ofstream(output/"selected.txt")<<chosen<<' '<<std::setprecision(12)<<selected<<'\n';
 std::ofstream activity(output/"activity.csv");
 activity<<"year,signature,active_pixels,area_m2,centroid_x_m,centroid_y_m\n";
 for(int year=a0;year<=a1;++year)for(auto mode:{std::string("B"),std::string("W")}) {
  auto file=processed/(std::to_string(year)+"_"+mode+".u8");
  if(!fs::exists(file))continue;
  auto v=read<uint8_t>(file,n);size_t count=0;double sx=0,sy=0;
  for(size_t p=0;p<n;++p)if(v[p]&&avMask[p]) {
   ++count;sx+=(p%g.width+.5)*g.dx;sy+=(p/g.width+.5)*(-g.dy);
  }
  activity<<year<<','<<mode<<','<<count<<','<<count*std::abs(g.dx*g.dy)<<','<<(count?sx/count:NaN)<<','<<(count?sy/count:NaN)<<'\n';
 }
}

void catalog(const fs::path& sites,const fs::path& output) {
 fs::create_directories(output);std::ifstream f(sites);
 if(!f)throw std::runtime_error("Missing permitted site metadata");
 std::ofstream out(output/"site_locations.csv");
 out<<"site_id,latitude_deg,longitude_deg,region,earth_x_m,earth_y_m,earth_z_m\n";
 std::string line;std::getline(f,line);
 const double pi=std::acos(-1.),radius=6371008.8;
 while(std::getline(f,line)) {
  auto v=split(line);if(v.size()!=3)continue;
  double lat=std::stod(v[1]),lon=std::stod(v[2]);
  std::string region=v[0][0]=='V'?"andes_north":v[0][0]=='B'?"andes_central":v[0][0]=='H'?"himalaya":"new_guinea";
  double a=lat*pi/180,b=lon*pi/180;
  out<<std::setprecision(12)<<v[0]<<','<<lat<<','<<lon<<','<<region<<','<<radius*std::cos(a)*std::cos(b)<<','<<radius*std::cos(a)*std::sin(b)<<','<<radius*std::sin(a)<<'\n';
 }
}

void compare_domains(const fs::path& small,const fs::path& large,const fs::path& output) {
 Grid a=grid(small),b=grid(large);
 if(a.epsg!=b.epsg||a.dx!=b.dx||a.dy!=b.dy)throw std::runtime_error("Comparison grids must share CRS and sampling");
 double fx=(a.x0-b.x0)/a.dx,fy=(a.y0-b.y0)/a.dy;
 long ox=std::lround(fx),oy=std::lround(fy);
 if(std::abs(fx-ox)>1e-7||std::abs(fy-oy)>1e-7||ox<0||oy<0||ox+long(a.width)>long(b.width)||oy+long(a.height)>long(b.height))throw std::runtime_error("Small comparison grid must nest exactly in large grid");
 std::ofstream out(output);out<<"year,signature,common_valid,small_positive,large_positive,intersection,union,IoU,agreement,mean_abs_RGB_difference\n";
 std::ifstream annual(large/"annual.csv");std::string line;std::getline(annual,line);
 while(std::getline(annual,line)) {
  auto year=split(line)[0];if(!fs::exists(small/(year+"_rgb.f32")))continue;
  auto ra=read<float>(small/(year+"_rgb.f32"),3*a.size()),rb=read<float>(large/(year+"_rgb.f32"),3*b.size());
  for(auto mode:{std::string("B"),std::string("W")}) {
   auto ma=read<uint8_t>(small/(year+"_"+mode+".u8"),a.size()),mb=read<uint8_t>(large/(year+"_"+mode+".u8"),b.size());
   size_t n=0,na=0,nb=0,inter=0,uni=0,equal=0;double diff=0;
   for(size_t y=0;y<a.height;++y)for(size_t x=0;x<a.width;++x) {
    size_t i=y*a.width+x,j=(y+oy)*b.width+x+ox;
    if(!std::isfinite(ra[i])||!std::isfinite(rb[j]))continue;
    ++n;na+=ma[i];nb+=mb[j];inter+=(ma[i]&&mb[j]);uni+=(ma[i]||mb[j]);equal+=(ma[i]==mb[j]);
    for(size_t band=0;band<3;++band)diff+=std::abs(ra[band*a.size()+i]-rb[band*b.size()+j]);
   }
   out<<year<<','<<mode<<','<<n<<','<<na<<','<<nb<<','<<inter<<','<<uni<<','<<ratio(inter,uni)<<','<<ratio(equal,n)<<','<<(n?diff/(3*n):NaN)<<'\n';
  }
 }
}
void statistics(const fs::path& sites,const fs::path& channels,const fs::path& derived,const fs::path& output) {
 fs::create_directories(output);
 std::map<std::string,std::vector<std::string>> geometry;
 std::ifstream cf(channels);std::string line;std::getline(cf,line);
 while(std::getline(cf,line)){auto v=split(line);if(v.size()==8)geometry[v[0]]=v;}
 std::ofstream data(output/"relationships.csv"),audit(output/"site_audit.csv"),groups(output/"morphology_summary.csv"),fit(output/"regression.csv");
 data<<"site_id,SR,width_m,distance_m,normalized_distance,slope,morphology\n";
 audit<<"site_id,ratio_available,channel_geometry_available,status\n";
 groups<<"morphology,n,min,q25,median,q75,max\n";
 fit<<"n,intercept_log10,slope_log10,r_squared\n";
 std::ifstream f(sites);std::getline(f,line);std::map<int,std::vector<double>> bytype;
 std::vector<double> xs,ys;
 while(std::getline(f,line)) {
  auto v=split(line);if(v.empty())continue;auto id=v[0];
  std::ifstream mf(derived/id/"event"/"selected.txt");std::string mode;double sr=NaN;
  bool have_ratio=bool(mf>>mode>>sr)&&std::isfinite(sr);
  bool have_geometry=geometry.count(id)>0;
  audit<<id<<','<<have_ratio<<','<<have_geometry<<','<<(have_ratio&&have_geometry?"independent_subset":"missing_independent_measurements")<<'\n';
  if(!have_ratio||!have_geometry)continue;
  auto&g=geometry[id];double w=std::stod(g[1]),d=std::stod(g[2]),zu=std::stod(g[3]),zd=std::stod(g[4]),len=std::stod(g[5]);int type=std::stoi(g[6]);
  if(w<=0||d<0||len<=0||type<1||type>3)throw std::runtime_error("Invalid independent channel geometry");
  double distance=d/w,slope=(zu-zd)/len;
  data<<id<<','<<sr<<','<<w<<','<<d<<','<<distance<<','<<slope<<','<<type<<'\n';
  bytype[type].push_back(sr);
  if(distance>60&&sr>0){xs.push_back(std::log10(distance));ys.push_back(std::log10(sr));}
 }
 for(auto&g:bytype)groups<<g.first<<','<<g.second.size()<<','<<quantile(g.second,0)<<','<<quantile(g.second,.25)<<','<<quantile(g.second,.5)<<','<<quantile(g.second,.75)<<','<<quantile(g.second,1)<<'\n';
 double a=NaN,b=NaN,r2=NaN;
 if(xs.size()>2){double xm=std::accumulate(xs.begin(),xs.end(),0.)/xs.size(),ym=std::accumulate(ys.begin(),ys.end(),0.)/ys.size();double xx=0,xy=0,yy=0;for(size_t i=0;i<xs.size();++i){xx+=(xs[i]-xm)*(xs[i]-xm);xy+=(xs[i]-xm)*(ys[i]-ym);yy+=(ys[i]-ym)*(ys[i]-ym);}if(xx>0&&yy>0){b=xy/xx;a=ym-b*xm;r2=xy*xy/(xx*yy);}}
 fit<<xs.size()<<','<<a<<','<<b<<','<<r2<<'\n';
}
void selftest(const fs::path& path) {
 if(!path.parent_path().empty())fs::create_directories(path.parent_path());
 std::ofstream out(path);out<<"test,calculated,expected,tolerance,pass\n";int failed=0;
 auto test=[&](std::string name,double got,double expected,double tol=1e-12){bool pass=std::isnan(expected)?std::isnan(got):std::abs(got-expected)<=tol;out<<name<<','<<std::setprecision(17)<<got<<','<<expected<<','<<tol<<','<<pass<<'\n';if(!pass)++failed;};
 test("median_odd",quantile({7,1,3},.5),3);test("median_even",quantile({9,1,3,5},.5),4);
 test("percentile_linear",quantile({0,10},.9),9);test("missing_removed",quantile({NaN,1,3},.5),2);test("all_missing",quantile({NaN},.5),NaN);
 test("reflectance_scale",reflectance(10000),.075);test("fill_missing",reflectance(0),NaN);
 test("clear_land",clear(64,0,8),1);test("clear_water",clear(128,0,8),1);test("cloud_rejected",clear(8,0,8),0);test("shadow_rejected",clear(16,0,8),0);test("saturation_rejected",clear(64,1,5),0);
 for(int sensor:{5,7,8})for(size_t j=0;j<6;++j){std::array<double,6> r{};r[j]=1;auto t=transform(r,sensor);for(size_t k=0;k<3;++k)test("basis_"+std::to_string(sensor)+"_"+std::to_string(j)+"_"+std::to_string(k),t[k],coefficients(sensor)[k][j]);}
 test("zero_spectrum",transform({0,0,0,0,0,0},5)[0],0);
 test("constant_scene_strict_threshold",1.>quantile({1,1,1},.9),0);
 test("identical_areas_SR1",ratio(7,7),1);test("empty_parent_undefined",ratio(3,0),NaN);test("empty_avulsion_SR0",ratio(0,9),0);test("area_scale_invariance",ratio(35,15),ratio(7,3));
 std::vector<std::array<double,2>> box={{{0,0}},{{2,0}},{{2,3}},{{0,3}}};int pixels=0;for(int y=0;y<5;++y)for(int x=0;x<5;++x)pixels+=inside(x+.5,y+.5,box);test("polygon_area_six_pixels",pixels,6);
 std::vector<int> first={1,0,1,0},second={0,1,1,0};int unique=0,sum=0;for(size_t i=0;i<4;++i){unique+=(first[i]+second[i])>0;sum+=first[i]+second[i];}test("temporal_union",unique,3);test("temporal_duration_sum",sum,4);
 out.close();if(failed)throw std::runtime_error(std::to_string(failed)+" failed checks");std::cout<<"All limiting-case checks passed\n";
}
int main(int argc,char**argv) {
 try {
  if(argc==3&&std::string(argv[1])=="selftest")selftest(argv[2]);
  else if(argc==4&&std::string(argv[1])=="analyze")analyze(argv[2],argv[3]);
  else if(argc==5&&std::string(argv[1])=="measure")measure(argv[2],argv[3],argv[4]);
  else if(argc==4&&std::string(argv[1])=="catalog")catalog(argv[2],argv[3]);
  else if(argc==6&&std::string(argv[1])=="statistics")statistics(argv[2],argv[3],argv[4],argv[5]);
  else if(argc==5&&std::string(argv[1])=="compare-domains")compare_domains(argv[2],argv[3],argv[4]);
  else{std::cerr<<"Usage: avulsion selftest OUTPUT.csv | analyze INPUT_DIR OUTPUT_DIR | measure PROCESSED_DIR ANNOTATIONS.csv OUTPUT_DIR\n";return 2;}
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}return 0;
}
