#include <gtest/gtest.h>

#include "vector.hpp"

namespace geo {

	TEST( Vector, stub ) {
		VectorF3 v{ 0.0f, 1.0f, 2.0f };

		EXPECT_EQ( 0.0f, v[0] );
		EXPECT_EQ( 1.0f, v[1] );
		EXPECT_EQ( 2.0f, v[2] );
	}

}
