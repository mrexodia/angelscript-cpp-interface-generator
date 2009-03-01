// this is just an example class
class Object
{
public:
  // Class method
  void method();
  
  // Overloaded assignment operator
  Object &operator=(const Object &);
  Object &operator=(int);
};
