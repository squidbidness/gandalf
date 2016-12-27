#include <gtest/gtest.h>

#include "vector.hpp"

#include <iostream>

namespace geo {

	using namespace Vector_shorthand;
	using namespace std;

	template< typename ...S >
	auto testComponents( S &&...s ) -> void {
		auto v = V_( std::forward<S>( s )... );

		if constexpr ( v.size() > 0 ) {
			EXPECT_EQ( v[0], v.x() )
					<< "v[0] = " << v[0] << ", v.x()=" << v.x();
		}
		if constexpr ( v.size() > 1 ) {
			EXPECT_EQ( v[1], v.y() )
					<< "v[1] = " << v[1] << ", v.y()=" << v.y();
		}
		if constexpr ( v.size() > 2 ) {
			EXPECT_EQ( v[2], v.z() )
					<< "v[2] = " << v[2] << ", v.z()=" << v.z();
		}
		if constexpr ( v.size() > 3 ) {
			EXPECT_EQ( v[3], v.w() )
					<< "v[3] = " << v[3] << ", v.w()=" << v.w();
		}
	}

	TEST( Vector, component_getters ) {

		testComponents( 0.0f );
		testComponents( 0.0f, 1.0f );
		testComponents( 0.0f, 1.0f, 2.0f );
		testComponents( 0.0f, 1.0f, 2.0f, 3.0f );

		testComponents( 0.0f );
		testComponents( 0.0f, 1.0f );
		testComponents( 0.0f, 1.0f, 2.0f );
		testComponents( 0.0f, 1.0f, 2.0f, 3.0f );

		testComponents( 0.0 );
		testComponents( 0.0, 1.0 );
		testComponents( 0.0, 1.0, 2.0 );
		testComponents( 0.0, 1.0, 2.0, 3.0 );

		testComponents( 0 );
		testComponents( 0, 1 );
		testComponents( 0, 1, 2 );
		testComponents( 0, 1, 2, 3 );

		testComponents( 0ul );
		testComponents( 0ul, 1ul );
		testComponents( 0ul, 1ul, 2ul );
		testComponents( 0ul, 1ul, 2ul, 3ul );
	}

	TEST( Vector, dot ) {
		EXPECT_EQ(
				4.0f,
				dot( V_(0.0f, 1.0f, 2.0f, 3.0f), V_(3.0f, 2.0f, 1.0f, 0.0f) )
				);
		EXPECT_EQ( 14.0, dot( V_(1.0, 2.0, 3.0), V_(1.0, 2.0, 3.0) ) );
		EXPECT_EQ( -2, dot( V_(4, -2), V_(-2, -3) ) );
		EXPECT_EQ( 14u, dot( V_(4, 2), V_(2, 3) ) );
	}


	TEST( Vector, forEachComponent ) {
		VectorF3 v1;
		forEachComponent( [] ( auto I, auto &v ) { v[I] = 10.0f; }, v1 );
		EXPECT_EQ( V_(10.0f, 10.0f, 10.0f), v1 );

		EXPECT_EQ(
				V_(10.0f, 40.0f, 90.0f, 160.0f),
				forEachComponent(
					[] ( auto I, auto const &a, auto const &b ) { return a[I] * b[I]; },
					V_(1.0f, 2.0f, 3.0f, 4.0f),
					V_(10.0f, 20.0f, 30.0f, 40.0f)
					)
				);
	}

}
