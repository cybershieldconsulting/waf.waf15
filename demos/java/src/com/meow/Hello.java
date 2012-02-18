package com.meow; // obligatory

public class Hello
{

	public static class Foo {

	}

	int m_var = 0;
	public Hello()
	{
		this.m_var = 2;
	}

	class MyHelperClass
	{
		MyHelperClass() { }
		int someHelperMethod(int z, int q) { return 2; }
	}

	public Object makeObj(String name)
	{
		final String objName = "My name is " + name;

		return new Object() {
			public String toString()
			{
				return objName;
			}
		};
	}

	public static void main(String args[])
	{
		System.out.println("Hello, world");
	}
}
